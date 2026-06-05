from app.database.mongodb import db
from app.modules.logger import logger
from app.modules.stt_manager import process_recording_to_text
from app.modules.zadarma_manager import fetch_call_recording_data


async def handle_start(pbx_id, data):
    await db.db["calls"].update_one(
        {"pbx_call_id": pbx_id},
        {"$set": {"status": "started", "start_data": data}},
        upsert=True
    )

async def handle_end(pbx_id, data):
    await db.db["calls"].update_one(
        {"pbx_call_id": pbx_id},
        {"$set": {"status": "ended", "end_data": data}},
        upsert=True
    )

async def handle_record(pbx_id, data):
    logger.info(data)

    event = payload.get("event")
    # unique ID of the call with the call recording
    call_id_with_rec = payload.get("call_id_with_rec")
    pbx_call_id = payload.get("pbx_call_id")
    caller_phone = payload.get("caller_id")

    data = await fetch_call_recording_data(call_id_with_rec)

    if data and "link" in data:
        text = await process_recording_to_text(data["link"], call_id_with_rec)
    #
    #     if text:
    #         save_stt_to_vector_db(caller_phone, text)
    #         logger.info(f"ZADARMA pbx_call_id: {pbx_call_id}")
    #         logger.info(f"ZADARMA call_id_with_rec: {call_id_with_rec}")
    #         # Fix me
    #         # await delete_recording_data(pbx_call_id)
    # else:
    #     logger.error(f"ABORTED | No download link available for call: {call_id_with_rec}")
