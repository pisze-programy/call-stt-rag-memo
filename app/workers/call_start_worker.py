from app.database.call_operations import initialize_call
from app.modules.kafka_client import get_consumer
from app.modules.logger import logger


def run_call_start_worker():
    consumer = get_consumer(
        "zadarma_start",
        "call_start_processing_group"
    )

    for message in consumer:
        try:
            payload = message.value
            logger.info(f"Received message: {payload}")

            pbx_call_id = payload.get("pbx_call_id")
            caller_id = payload.get("caller_id")
            called_did = payload.get("called_did")
            call_start = payload.get("call_start")

            initialize_call(pbx_call_id, caller_id, called_did, call_start)
            consumer.commit()
        except Exception as e:
            logger.error(f"Worker call_start_worker error: {e}", exc_info=True)

if __name__ == "__main__":
    run_call_start_worker()