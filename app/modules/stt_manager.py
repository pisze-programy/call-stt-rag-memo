import io
import os

import aiofiles
import aiohttp
import httpx
from openai import AsyncOpenAI

from app.modules.logger import logger


async def process_recording_to_text(local_path: str, call_id_with_rec: str) -> str:
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async with httpx.AsyncClient() as http_client:
        try:
            with open(local_path, "rb") as audio_file:
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


async def save_file_locally(url: str, local_path: str):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(local_path, mode='wb') as f:
                    while True:
                        chunk = await response.content.read(512 * 1024)
                        if not chunk:
                            break
                        await f.write(chunk)
            else:
                raise Exception(f"Failed to download file, status: {response.status}")