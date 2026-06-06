from app.database.call_operations import finalize_call
from app.modules.kafka_client import get_consumer
from app.modules.logger import logger


def run_call_end_worker():
    consumer = get_consumer(
        "zadarma_end",
        "call_end_processing_group"
    )

    for message in consumer:
        try:
            payload = message.value
            logger.info(f"Received message: {payload}")
            pbx_call_id = payload.get("pbx_call_id")
            duration = payload.get("duration")
            raw_recorded_status = payload.get("is_recorded")
            is_recorded = (raw_recorded_status == "1")

            finalize_call(pbx_call_id, duration, is_recorded)
            consumer.commit()
        except Exception as e:
            logger.error(f"Worker call_end_worker error: {e}", exc_info=True)

if __name__ == "__main__":
    run_call_end_worker()