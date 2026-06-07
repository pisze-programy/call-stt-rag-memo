import asyncio
import os

from dotenv import load_dotenv

from app.database.call_operations import update_call_recording_link, update_call_transcription
from app.database.mongodb import db
from app.modules.kafka_client import KafkaManager
from app.modules.logger import logger
from app.modules.stt_manager import process_recording_to_text, save_stt_to_vector_db, save_file_locally
from app.modules.zadarma_manager import fetch_call_recording_data
from app.workers.kafka_worker import KafkaWorker

load_dotenv()


async def handle_call_record(payload):
    call_id_with_rec = payload.get("call_id_with_rec")
    pbx_call_id = payload.get("pbx_call_id")
    caller_phone = payload.get("caller_id")

    local_path = f"/app/data/recordings/{pbx_call_id}.wav"

    data = await fetch_call_recording_data(call_id_with_rec)
    if not data or "link" not in data:
        logger.error(f"ABORTED | No download link for: {call_id_with_rec}")
        return

    await save_file_locally(data["link"], local_path)
    await update_call_recording_link(pbx_call_id, local_path)

    text = await process_recording_to_text(local_path, pbx_call_id)

    if text:
        await update_call_transcription(pbx_call_id, text)
        save_stt_to_vector_db(caller_phone, text)


async def main():
    await db.connect(os.getenv("MONGO_URI"), "memo_store")
    consumer = KafkaManager.get_consumer("zadarma_record", "recording_processing_group")
    worker = KafkaWorker(consumer, handle_call_record)
    try:
        await worker.start()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())