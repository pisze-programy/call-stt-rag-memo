import asyncio
import json

from dotenv import load_dotenv

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

        logger.info(f"classify response: {text} {caller_id} {result}")

        if intent == 'SAVE_NOTE':
            return None
        elif intent == 'BIND_EMAIL':
            return None
        elif intent == 'QUERY_NOTES':
            return None
        else:
            logger.info(f"SMS ignored or invalid: {text}")
    except (json.JSONDecodeError, KeyError, AssertionError) as e:
        logger.error(f"Invalid LLM response: {text}, error: {e}")


if __name__ == "__main__":
    asyncio.run(run_worker("zadarma_sms", "sms_processing_group", handle_sms))