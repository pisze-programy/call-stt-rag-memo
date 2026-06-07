import asyncio
import os

from app.database.call_operations import finalize_call
from app.database.mongodb import db
from app.modules.kafka_client import KafkaManager
from app.modules.logger import logger
from app.workers.kafka_worker import KafkaWorker


async def handle_call_end(payload):
    logger.info(f"Received message: {payload}")
    pbx_call_id = payload.get("pbx_call_id")
    duration = payload.get("duration")
    raw_recorded_status = payload.get("is_recorded")
    is_recorded = (raw_recorded_status == "1")

    await finalize_call(pbx_call_id, duration, is_recorded)

async def main():
    await db.connect(os.getenv("MONGO_URI"), "memo_store")
    consumer = KafkaManager.get_consumer("zadarma_end", "call_end_processing_group")
    worker = KafkaWorker(consumer, handle_call_end)
    try:
        await worker.start()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())