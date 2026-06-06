import asyncio

from app.modules.kafka_client import get_consumer
from app.modules.logger import logger
from app.modules.stt_manager import process_recording_to_text, save_stt_to_vector_db
from app.modules.zadarma_manager import fetch_call_recording_data


def process_event(payload):
    event = payload.get("event")
    logger.info(f"ZADARMA event: {event}")
    
    call_id_with_rec = payload.get("call_id_with_rec")
    pbx_call_id = payload.get("pbx_call_id")
    caller_phone = payload.get("caller_id")

    data = asyncio.run(fetch_call_recording_data(call_id_with_rec))

    if data and "link" in data:
        text = asyncio.run(process_recording_to_text(data["link"], call_id_with_rec))
        if text:
            save_stt_to_vector_db(caller_phone, text)
            logger.info(f"ZADARMA pbx_call_id: {pbx_call_id}")
            logger.info(f"ZADARMA call_id_with_rec: {call_id_with_rec}")
    else:
        logger.error(f"ABORTED | No download link available for call: {call_id_with_rec}")

async def run_record_worker(pbx_id, data):
    logger.info(f"record_worker {pbx_id} {data}")

    consumer = get_consumer(
        "zadarma_record"
    )

    for message in consumer:
        process_event(message.value)


if __name__ == "__main__":
    run_record_worker()