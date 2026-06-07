import asyncio

from dotenv import load_dotenv

load_dotenv()

from app.database.call_operations import initialize_call
from app.modules.logger import logger
from app.workers.kafka_worker import KafkaWorker

async def handle_call_start(payload):
    logger.info(f"Received message: {payload}")

    pbx_call_id = payload.get("pbx_call_id")
    caller_id = payload.get("caller_id")
    called_did = payload.get("called_did")
    call_start = payload.get("call_start")

    await initialize_call(pbx_call_id, caller_id, called_did, call_start)


if __name__ == "__main__":
    asyncio.run(KafkaWorker.run_worker("zadarma_start", "call_start_processing_group", handle_call_start))