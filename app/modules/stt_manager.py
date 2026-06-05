import io
import os

import httpx
from openai import AsyncOpenAI

from app.modules.logger import logger


async def process_recording_to_text(download_url: str, call_id_with_rec: str) -> str:
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async with httpx.AsyncClient() as http_client:
        try:
            response = await http_client.get(download_url)
            if response.status_code != 200:
                logger.error(f"DOWNLOAD FAILED: {response.status_code}")
                return ""

            audio_bytes = response.content
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = f"{call_id_with_rec}.mp3"

            transcription = await openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pl"
            )

            logger.info(f"STT SUCCESS | TEXT: {transcription.text}")
            return transcription.text

        except Exception as e:
            logger.error(f"STT PROCESSING ERROR: {str(e)}")
            return ""

def save_stt_to_vector_db(caller_phone: str, text: str) -> bool:
    logger.info(f"save_to_vector_db: {caller_phone}, {text}")
    return True