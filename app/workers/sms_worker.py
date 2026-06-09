import asyncio

from dotenv import load_dotenv

load_dotenv()

from app.modules.logger import logger

from app.workers.kafka_worker import run_worker


async def handle_sms(payload: dict):
    await asyncio.sleep(0)
    logger.info(f"Received message: {payload}")
    # TODO: upgrade zadarma subscription to get sms available
    # payload = {"event": event, "from": from_number, "message_text": message_text}
    # text = process_recording_to_text(data["link"], call_id_with_rec))
    #
    # if text:
    #     save_stt_to_vector_db(caller_id, text)
    #     logger.info(f"ZADARMA pbx_call_id: {pbx_call_id}")
    #     logger.info(f"ZADARMA call_id_with_rec: {call_id_with_rec}")


if __name__ == "__main__":
    asyncio.run(run_worker("zadarma_sms", "sms_processing_group", handle_sms))