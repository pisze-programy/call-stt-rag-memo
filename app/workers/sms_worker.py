from app.modules.kafka_client import get_consumer
from app.modules.logger import logger


def run_sms_worker():
    consumer = get_consumer("zadarma_sms", "sms_processing_group")

    for message in consumer:
        payload = message.value
        logger.info(f"Received message: {payload}")

if __name__ == "__main__":
    run_sms_worker()