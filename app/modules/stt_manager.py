import json
import os
import uuid

import aiofiles
import aiohttp
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from app.database.qdrant import qdrant
from app.models.Interpretation import Interpretation
from app.modules.logger import logger

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def process_recording_to_text(local_path: str,) -> str:
    try:
        with open(local_path, "rb") as audio_file:
            transcription = await openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pl"
            )

        logger.info(f"STT SUCCESS | TEXT: {transcription.text}")
        return transcription.text

    except Exception as e:
        logger.error(f"STT PROCESSING ERROR: {str(e)}")
        return ""

async def save_stt_to_vector_db(
    caller_phone: str,
    pbx_call_id: str,
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
                    "caller_phone": caller_phone,
                    "pbx_call_id": pbx_call_id,
                    "text": text,
                    "summary": interpretation.summary,
                    "note_type": interpretation.note_type,
                    "people": interpretation.people,
                }
            }
        ]
    )


async def interpret_transcription(transcription: str) -> Interpretation:
    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            ChatCompletionSystemMessageParam(
                role="system",
                content="""
                    Your task is to transform ANY user transcription into a strict JSON structure optimized for:
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
                content=transcription
            )
        ]
    )

    return Interpretation.model_validate(
        json.loads(response.choices[0].message.content)
    )

async def embed_text(text: str) -> list[float]:
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding


async def save_file_locally(url: str, local_path: str):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(local_path, mode='wb') as f:
                    while True:
                        chunk = await response.content.read(512 * 1024)
                        if not chunk:
                            break
                        await f.write(chunk)
            else:
                raise Exception(f"Failed to download file, status: {response.status}")