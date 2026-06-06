import asyncio

from app.database.call_operations import update_call_recording_link, update_call_transcription
from app.modules.kafka_client import get_consumer
from app.modules.logger import logger
from app.modules.stt_manager import process_recording_to_text, save_stt_to_vector_db, save_file_locally
from app.modules.zadarma_manager import fetch_call_recording_data


async def process_event(payload):
    call_id_with_rec = payload.get("call_id_with_rec")
    pbx_call_id = payload.get("pbx_call_id")
    caller_phone = payload.get("caller_id")

    local_path = f"/app/data/recordings/{pbx_call_id}.wav"

    try:
        data = await fetch_call_recording_data(call_id_with_rec)
        if not data or "link" not in data:
            logger.error(f"ABORTED | No download link for: {call_id_with_rec}")
            return

        await save_file_locally(data["link"], local_path)
        update_call_recording_link(pbx_call_id, local_path)

        try:
            text = await process_recording_to_text(local_path, pbx_call_id)
            if text:
                update_call_transcription(pbx_call_id, text)
                save_stt_to_vector_db(caller_phone, text)
        except Exception as stt_err:
            logger.error(f"STT FAILED | call: {pbx_call_id} | error: {stt_err}")

    except Exception as e:
        logger.error(f"DOWNLOAD/DB FAILED | call: {pbx_call_id} | error: {e}", exc_info=True)

def run_call_record_worker():
    consumer = get_consumer(
        "zadarma_record",
        "recording_processing_group"
    )

    for message in consumer:
        process_event(message.value)
        consumer.commit()


if __name__ == "__main__":
    run_call_record_worker()