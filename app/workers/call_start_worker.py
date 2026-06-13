import asyncio

from dotenv import load_dotenv

from app.database.caller_operations import upsert_caller
from app.modules.memory_manager import normalize_phone_smart

load_dotenv()

from app.database.call_operations import initialize_call
from app.modules.logger import logger
from app.workers.kafka_worker import run_worker


async def handle_call_start(payload):
    logger.info(f"Received message: {payload}")

    pbx_call_id = payload.get("pbx_call_id")
    caller_id = payload.get("caller_id")
    called_did = payload.get("called_did")
    call_start = payload.get("call_start")
    internal = payload.get("internal")
    phone = normalize_phone_smart(caller_id)

    if phone is None:
        return

    await initialize_call(pbx_call_id, phone, called_did, call_start, internal)
    await upsert_caller(phone)


if __name__ == "__main__":
    asyncio.run(run_worker("zadarma_start", "call_start_processing_group", handle_call_start))