import asyncio
import os

from dotenv import load_dotenv

from app.database.qdrant import init_qdrant
from app.models.Interpretation import Interpretation

load_dotenv()

from app.database.call_operations import update_call_recording_link, update_call_transcription
from app.modules.logger import logger
from app.modules.stt_manager import process_recording_to_text, save_stt_to_vector_db, save_file_locally, embed_text, \
    interpret_transcription
from app.modules.zadarma_manager import fetch_call_recording_data
from app.workers.kafka_worker import run_worker


async def handle_call_record(payload):
    call_id_with_rec = payload.get("call_id_with_rec")
    pbx_call_id = payload.get("pbx_call_id")
    caller_phone = payload.get("caller_id")

    data = await fetch_call_recording_data(call_id_with_rec)
    if not data or "link" not in data:
        logger.error(f"ABORTED | No download link for: {call_id_with_rec}")
        return

    ext = os.path.splitext(data["link"])[1]
    if not ext or ext not in ['.mp3', '.wav', '.ogg', '.m4a']:
        ext = ".mp3"
    local_path = f"/app/data/recordings/{pbx_call_id}{ext}"

    await save_file_locally(data["link"], local_path)
    await update_call_recording_link(pbx_call_id, local_path)

    text = await process_recording_to_text(local_path)

    if text:
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
            interpretation = await interpret_transcription(text)
        except Exception as e:
            logger.error(f"Note Interpretation error: {str(e)}")
        await update_call_transcription(pbx_call_id, text, interpretation)
        embedding = await embed_text(text)
        await save_stt_to_vector_db(
            caller_phone,
            pbx_call_id,
            text,
            embedding,
            interpretation
        )

if __name__ == "__main__":
    asyncio.run(init_qdrant())
    asyncio.run(run_worker("zadarma_record", "recording_processing_group", handle_call_record))