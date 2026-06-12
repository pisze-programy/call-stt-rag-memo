import asyncio
import json

from dotenv import load_dotenv

from app.modules.kafka_client import send_event
from app.modules.sms_manager import classify_sms_intent

load_dotenv()

from app.modules.logger import logger

from app.workers.kafka_worker import run_worker


async def handle_sms(payload: dict):
    await asyncio.sleep(0)
    logger.info(f"Received message: {payload}")
    # worker - sms - 1 | 2026 - 06 - 12
    # 12: 01:49, 414[INFO]
    # app: Received
    # message: {'event': 'SMS', 'result': '{"caller_did":"48573504251","caller_id":"48519661980","text":"Test"}'}

    result = json.loads(payload.get('result', '{}'))
    text = result.get('text', '')
    caller_id = result.get('caller_id')

    if (caller_id is None) or (text is None):
        logger.info(f"SMS ignored or invalid: {text}")
        return

    schema = await classify_sms_intent(text)

    logger.info(f"classify response: {text} {caller_id} {schema}")

    if schema.intent == 'SAVE_NOTE':
        return
    elif schema.intent == 'BIND_EMAIL':
        return
    elif schema.intent == 'QUERY_NOTES':
        return
    else:
        logger.info(f"SMS ignored or invalid: {text}")


if __name__ == "__main__":
    asyncio.run(run_worker("zadarma_sms", "sms_processing_group", handle_sms))