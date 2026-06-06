from app.modules.kafka_client import get_consumer
from app.modules.logger import logger


def run_sms_worker():
    consumer = get_consumer("zadarma_sms", "sms_processing_group")

    for message in consumer:
        payload = message.value
        logger.info(f"Received message: {payload}")
        # payload = {"event": event, "from": from_number, "message_text": message_text}
        # text = process_recording_to_text(data["link"], call_id_with_rec))
        #
        # if text:
        #     save_stt_to_vector_db(caller_phone, text)
        #     logger.info(f"ZADARMA pbx_call_id: {pbx_call_id}")
        #     logger.info(f"ZADARMA call_id_with_rec: {call_id_with_rec}")
        #     consumer.commit()

if __name__ == "__main__":
    run_sms_worker()