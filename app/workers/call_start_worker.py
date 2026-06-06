from app.modules.kafka_client import get_consumer
from app.modules.logger import logger


def run_call_start_worker():
    consumer = get_consumer(
        "zadarma_start"
    )
    for message in consumer:
        payload = message.value
        logger.info(f"Received message: {payload}")

if __name__ == "__main__":
    run_call_start_worker()