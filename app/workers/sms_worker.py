import asyncio
import json

from dotenv import load_dotenv
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.database.caller_operations import upsert_caller, update_email
from app.database.qdrant import qdrant, COLLECTION_NAME
from app.modules.memory_manager import save_to_vector_db, interpret_input, embed_text, interpret_search_query
from app.modules.sms_manager import classify_sms_intent

load_dotenv()

from app.modules.logger import logger

from app.workers.kafka_worker import run_worker


async def handle_sms(payload: dict):
    await asyncio.sleep(0)
    logger.info(f"Received message: {payload}")
    result = json.loads(payload.get('result', '{}'))
    text = result.get('text', '')
    caller_id = result.get('caller_id')

    if (caller_id is None) or (text is None):
        logger.info(f"SMS ignored or invalid: {text}")
        return None

    if not text or not text.strip():
        return {"intent": "REJECT", "email": None, "note_content": None, "query": None}

    try:
        result = await classify_sms_intent(text)
        intent = result.intent
        email = result.email

        logger.info(f"classify response: {text} {caller_id} {result}")

        if intent == 'SAVE_NOTE':
            try:
                interpretation = await interpret_input(text)
                embedding = await embed_text(text)

                await save_to_vector_db(
                    caller_id,
                    text,
                    embedding,
                    interpretation
                )
            except Exception as e:
                logger.error(f"Note Interpretation error: {str(e)}")
                return None
        elif intent == 'BIND_EMAIL':
            if email is None:
                return None
            await upsert_caller(caller_id)
            await update_email(caller_id, email)
        elif intent == 'QUERY_NOTES':
            query_vector = await embed_text(text)
            limit = 5

            results = qdrant.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                query_filter=Filter(
                    must=[FieldCondition(key="caller_id", match=MatchValue(value=caller_id))]
                ),
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )

            sorted_points = sorted(results.points, key=lambda x: x.payload.get("created_at", 0))
            context_list = [f"--- NOTE START ---\n{hit.payload.get('text', '')}" for hit in sorted_points]
            context = "\n\n".join(context_list)
            answer = await interpret_search_query(text, context)
            logger.info(f"Query result: {answer}")
            return None
        else:
            logger.info(f"SMS ignored or invalid: {text}")
    except (json.JSONDecodeError, KeyError, AssertionError) as e:
        logger.error(f"Invalid LLM response: {text}, error: {e}")


if __name__ == "__main__":
    asyncio.run(run_worker("zadarma_sms", "sms_processing_group", handle_sms))