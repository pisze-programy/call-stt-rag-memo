import asyncio

from dotenv import load_dotenv

load_dotenv()

from app.database.call_operations import finalize_call
from app.modules.logger import logger
from app.workers.kafka_worker import KafkaWorker

async def handle_call_end(payload):
    logger.info(f"Received message: {payload}")
    pbx_call_id = payload.get("pbx_call_id")
    duration = payload.get("duration")
    raw_recorded_status = payload.get("is_recorded")
    is_recorded = (raw_recorded_status == "1")

    await finalize_call(pbx_call_id, duration, is_recorded)

if __name__ == "__main__":
    asyncio.run(KafkaWorker.run_worker("zadarma_end", "call_end_processing_group", handle_call_end))