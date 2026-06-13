import json
import os
import uuid
from datetime import datetime

import phonenumbers
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from openai.types.chat.completion_create_params import ResponseFormat
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.database.qdrant import qdrant, COLLECTION_NAME
from app.models.Interpretation import Interpretation
from app.modules.kafka_client import send_event
from app.modules.logger import logger

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def save_to_vector_db(
        caller_id: str,
        text: str,
        embedding: list[float],
        interpretation: Interpretation
):
    point_id = str(uuid.uuid4())
    qdrant.upsert(
        collection_name=os.getenv("QDRANT_COLLECTION"),
        points=[
            {
                "id": point_id,
                "vector": embedding,
                "payload": {
                    "caller_id": caller_id,
                    "text": text,
                    "summary": interpretation.summary,
                    "note_type": interpretation.note_type,
                    "people": interpretation.people,
                    "created_at": datetime.now().isoformat(),
                }
            }
        ]
    )


async def interpret_input(input: str) -> Interpretation:
    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_format=ResponseFormat(type="json_object"),
        messages=[
            ChatCompletionSystemMessageParam(
                role="system",
                content="""
                    Your task is to transform ANY user text into a strict JSON structure optimized for:
                    - semantic search (vector databases)
                    - retrieval filtering per user
                    - long-term memory storage

                    ---

                    CRITICAL RULES:
                    - Do NOT invent or infer missing facts.
                    - Do NOT assume names, dates, or intent.
                    - If information is missing, use null or [].
                    - Output MUST be valid JSON only — no markdown fences, no preamble.
                    - Keep language neutral.

                    ---

                    CLASSIFICATION:
                    Classify the input into exactly one:
                    - event     (something happened: trip, cinema, dinner, activity)
                    - meeting   (interaction with one or more people)
                    - task      (something to do or remember)
                    - fact      (general statement or observation)
                    - person    (note about a person)
                    - place     (note about a location)
                    - other

                    ---

                    FIELD ENUMS:

                    locations[].type     → "city" | "venue" | "address" | "region" | "country" | "other"
                    time_reference.relative → "past" | "present" | "future" | null
                    sentiment            → "positive" | "negative" | "neutral" | "mixed" | null
                                           (set null if not clearly expressed by the user)

                    activity.verb        → English infinitive form, e.g. "go to cinema", "meet", "visit"

                    ---

                    OUTPUT SCHEMA:

                    {
                      "note_type": "",
                      "activity": {
                        "verb": null,
                        "object": null,
                        "outcome": null
                      },
                      "people": [],
                      "locations": [],
                      "time_reference": {
                        "raw": null,
                        "resolved": null,
                        "relative": null
                      },
                      "sentiment": null,
                      "summary": "",
                      "entities": [],
                      "vector_string": ""
                    }

                    When people or locations are present, use this shape:

                    "people": [{ "name": "string", "role": "string", "notes": "string | null" }]
                    "locations": [{ "name": "string", "type": "string" }]

                    ---

                    VECTOR STRING RULES:
                    - Used ONLY for semantic embedding retrieval.
                    - Compact keyword list — NOT a sentence.
                    - Include: note_type, action verbs, people names, places, domain terms.
                    - Do NOT include user IDs, phone numbers, or full sentences.

                    ---

                    SUMMARY RULES:
                    - 1–2 sentences max.
                    - Factual, no interpretation, no hallucinations.

                    ---
                    """
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=input
            )
        ]
    )

    return Interpretation.model_validate(
        json.loads(response.choices[0].message.content)
    )


async def interpret_search_query(user_query: str, context: str) -> str:
    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            ChatCompletionSystemMessageParam(
                role="system",
                content=""
                        "You are a memory assistant. You are analyzing one or more notes about the user's life. "
                        "The provided context might contain multiple notes about the same topic or activity. "
                        "If these notes mention conflicting facts, figures, or details, prioritize the information "
                        "that is more specific, detailed, or implies a more recent state. "
                        "Do not treat all notes as equal facts if they contradict each other; instead, "
                        "treat them as a timeline where later or more precise data supersedes older, less accurate entries. "
                        "Synthesize the findings to present the most current and accurate status. "
                        "If notes contain conflicting information, explicitly highlight the ambiguity."
                        "Do not infer or estimate values; if a value is not explicitly stated, report it as missing."
                        "Always end your response with one short, natural follow-up question (hook) related to the topic. "
                        "Respond in the language of the user's question."
                        "",
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=""
                        f"User question: {user_query}\n\n"
                        f"Notes context (ordered from newest to oldest): {context}\n\n"
                        "Answer:"
                        ""
            )
        ]
    )

    return response.choices[0].message.content


async def refine_search_query(text: str) -> str:
    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            ChatCompletionSystemMessageParam(
                role="system",
                content=""
                        "You are a search query optimizer for vector databases. "
                        "Transform the user query into a concise, semantically rich keyword string. "
                        "Remove filler words, greetings, and conversational nuances. "
                        "Include names, places, dates, and domain-specific terms. "
                        "Return ONLY the optimized query string. "
                        "Detect the language of the user query and respond in the same language."
                        "",
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=f"User query: {text}"
            )
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


async def embed_text(text: str) -> list[float]:
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding


def normalize_phone_smart(phone_number: str | None) -> str | None:
    if phone_number is None:
        return None
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number.lstrip('+')

    try:
        number_obj = phonenumbers.parse(phone_number, None)
        if phonenumbers.is_valid_number(number_obj):
            return phonenumbers.format_number(number_obj, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        return None

    return phone_number

async def notify_user(phone: str, subject: str, body: str):
    await send_event("mail", {
        "caller_id": phone,
        "subject": subject,
        "body": body
    })

async def perform_vector_search(phone: str, text: str) -> str:
    refined_query = await refine_search_query(text)
    query_vector = await embed_text(refined_query)

    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=Filter(
            must=[FieldCondition(key="caller_id", match=MatchValue(value=phone))]
        ),
        limit=5,
        with_payload=True,
        with_vectors=False,
    )

    sorted_points = sorted(results.points, key=lambda x: x.payload.get("created_at", 0))
    context_list = [f"--- NOTE START (Score: {hit.score:.3f}) ---\n{hit.payload.get('text', '')}" for hit in
                    sorted_points]
    context = "\n\n".join(context_list)

    answer = await interpret_search_query(text, context)
    return answer

async def interpret_event_details(text: str):
    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            ChatCompletionSystemMessageParam(
                role="system",
                content="""
                    Extract Google Calendar event details from the user's notes.
                    The current timestamp is provided at the end of the user's message — use it as the reference point for relative dates (e.g. "today", "tomorrow", "next Monday").
                    
                    Return a JSON object with exactly these fields:
                    
                    {
                        "summary": "<string>",
                        "start_time": "<ISO-8601 string | null>",
                        "end_time": "<ISO-8601 string | null>",
                        "description": "<string | null>"
                    }
                    
                    Rules:
                    - summary: short title derived from the note's main topic. Null if nothing relevant.
                    - start_time / end_time: ISO-8601 with timezone offset if inferable, otherwise UTC. Set both to null if no date or time is mentioned.
                    - description: any remaining context, details, or notes not captured in summary. Null if nothing relevant.
                    - Output raw JSON only — no markdown, no explanation, no extra keys.
                """
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=f"User's notes: {text} and current timestamp is {datetime.now().isoformat()}"
            )
        ]
    )

    logger.info(f"interpret_event_details response: {response.choices[0].message.content}")

    return json.loads(response.choices[0].message.content)