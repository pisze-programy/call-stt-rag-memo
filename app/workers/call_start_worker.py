import asyncio
import os

from app.database.call_operations import initialize_call
from app.database.mongodb import db
from app.modules.kafka_client import KafkaManager
from app.modules.logger import logger
from app.workers.kafka_worker import KafkaWorker


async def handle_call_start(payload):
    logger.info(f"Received message: {payload}")

    pbx_call_id = payload.get("pbx_call_id")
    caller_id = payload.get("caller_id")
    called_did = payload.get("called_did")
    call_start = payload.get("call_start")

    await initialize_call(pbx_call_id, caller_id, called_did, call_start)


async def main():
    await db.connect(os.getenv("MONGO_URI"), "memo_store")
    consumer = KafkaManager.get_consumer("zadarma_start", "call_start_processing_group")
    worker = KafkaWorker(consumer, handle_call_start)
    try:
        await worker.start()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())