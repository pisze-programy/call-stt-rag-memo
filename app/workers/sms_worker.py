import asyncio
import os

from dotenv import load_dotenv

from app.database.mongodb import db
from app.modules.kafka_client import KafkaManager
from app.modules.logger import logger
from app.workers.kafka_worker import KafkaWorker

load_dotenv()

def handle_sms(payload: dict):
    logger.info(f"Received message: {payload}")
    # TODO: upgrade zadarma subscription to get sms available
    # payload = {"event": event, "from": from_number, "message_text": message_text}
    # text = process_recording_to_text(data["link"], call_id_with_rec))
    #
    # if text:
    #     save_stt_to_vector_db(caller_phone, text)
    #     logger.info(f"ZADARMA pbx_call_id: {pbx_call_id}")
    #     logger.info(f"ZADARMA call_id_with_rec: {call_id_with_rec}")


async def main():
    await db.connect(os.getenv("MONGO_URI"), "memo_store")
    consumer = KafkaManager.get_consumer("zadarma_sms", "sms_processing_group")
    worker = KafkaWorker(consumer, handle_sms)
    try:
        await worker.start()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())