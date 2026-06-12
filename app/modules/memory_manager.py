import json
import os
import uuid
from datetime import datetime

import phonenumbers
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from app.database.qdrant import qdrant
from app.models.Interpretation import Interpretation

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
                    "created_at": datetime.now(),
                }
            }
        ]
    )


async def interpret_input(input: str) -> Interpretation:
    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
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
                    - Include: note_type, action verbs, people names, places, domain terms, PL+EN if natural.
                    - Do NOT include user IDs, phone numbers, or full sentences.
                    - Example: "meeting work project collaboration Tomek spotkanie praca projekt"

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