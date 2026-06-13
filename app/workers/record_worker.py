import asyncio
import os

from dotenv import load_dotenv

from app.database.qdrant import init_qdrant
from app.models.Interpretation import Interpretation
from app.modules.memory_manager import interpret_input, embed_text, save_to_vector_db, normalize_phone_smart, \
    notify_user, refine_search_query, perform_vector_search

load_dotenv()

from app.database.call_operations import update_call_recording_link, update_call_transcription, get_call_by_pbx_id
from app.modules.logger import logger
from app.modules.stt_manager import process_recording_to_text, save_file_locally
from app.modules.zadarma_manager import fetch_call_recording_data
from app.workers.kafka_worker import run_worker


async def action_save_note(pbx_call_id: str, caller_id: str, text: str):
    interpretation: Interpretation = Interpretation(
        note_type="unknown",
        activity=None,
        people=[],
        locations=[],
        time_reference=None,
        sentiment=None,
        summary=text,
        entities=[],
        vector_string=text
    )

    try:
        interpretation = await interpret_input(text)
    except Exception as e:
        logger.error(f"Note Interpretation error: {str(e)}")

    await update_call_transcription(pbx_call_id, text, interpretation.model_dump())

    embedding = await embed_text(text)

    phone = normalize_phone_smart(caller_id)

    if phone is None:
        print(f"No phone number, pbx_call_id: {pbx_call_id}")
        return

    await save_to_vector_db(
        phone,
        text,
        embedding,
        interpretation
    )
    await notify_user(phone, "Call Processed", f"Your call has been transcribed and saved. {text}")

async def action_search_note(pbx_call_id: str, caller_id: str, text: str):
    phone = normalize_phone_smart(caller_id)

    interpretation = await refine_search_query(text)
    await update_call_transcription(pbx_call_id, text, interpretation)

    if phone is None:
        print(f"No phone number, pbx_call_id: {pbx_call_id}")
        return None

    answer = await perform_vector_search(phone, interpretation)
    logger.info(f"Query result: {answer}")
    await notify_user(phone, "Query Result", answer)
    return None

async def action_add_calendar(pbx_call_id: str, text: str):
    logger.debug(f"Phone number: {pbx_call_id} {text}")
    return None


async def handle_call_record(payload):
    logger.info(f"Received message: {payload}")
    call_id_with_rec = payload.get("call_id_with_rec")
    pbx_call_id = payload.get("pbx_call_id")

    data = await fetch_call_recording_data(call_id_with_rec)
    if not data or "link" not in data:
        logger.error(f"ABORTED | No download link for: {call_id_with_rec}")
        return None

    ext = os.path.splitext(data["link"])[1]
    if not ext or ext not in ['.mp3', '.wav', '.ogg', '.m4a']:
        ext = ".mp3"
    local_path = f"/app/data/recordings/{pbx_call_id}{ext}"

    await save_file_locally(data["link"], local_path)
    await update_call_recording_link(pbx_call_id, local_path)

    text = await process_recording_to_text(local_path)

    call_session_data = await get_call_by_pbx_id(pbx_call_id)
    internal = call_session_data["internal"]
    caller_id = call_session_data["caller_id"]

    if not text:
        logger.info(f"No text for {pbx_call_id}")
        return None

    if internal == "100":
        await action_save_note(pbx_call_id, caller_id, text)
    elif internal == "200":
        await action_search_note(pbx_call_id, caller_id, text)
    elif internal == "300":
        await action_add_calendar(pbx_call_id, text)
    return None


if __name__ == "__main__":
    init_qdrant()
    asyncio.run(run_worker("zadarma_record", "recording_processing_group", handle_call_record))