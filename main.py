import base64
import hashlib
import hmac
import io
import logging
import os
import sys

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request, Response
from openai import AsyncOpenAI

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()
load_dotenv()


def generate_auth_header(method: str, params_str: str, secret: str, key: str) -> str:
    # https://zadarma.com/en/support/api/#intro_authorization
    md5_hash = hashlib.md5(params_str.encode("utf-8")).hexdigest()
    data_to_sign = f"{method}{params_str}{md5_hash}"
    hmac_hex = hmac.new(
        secret.encode("utf-8"),
        data_to_sign.encode("utf-8"),
        hashlib.sha1
    ).hexdigest()
    base64_signature = base64.b64encode(hmac_hex.encode("utf-8")).decode("utf-8")
    return f"{key}:{base64_signature}"


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


async def fetch_call_recording_data(call_id: str):
    # https://zadarma.com/en/support/api/#api_pbx_record_request
    api_method = "/v1/pbx/record/request/"
    params = {"call_id": call_id}
    sorted_params = sorted(params.items())
    params_str = "".join(f"{k}={v}" for k, v in sorted_params)
    auth_header = generate_auth_header(api_method, params_str, os.getenv("ZADARMA_SECRET"), os.getenv("ZADARMA_KEY"))
    headers = {"Authorization": auth_header}
    url = f"{os.getenv('ZADARMA_API_URL')}{api_method}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"ZADARMA API RESPONSE: {data}")
                await process_recording_to_text(data["link"], call_id)
                return data
            else:
                logger.error(f"ZADARMA API ERROR: {response.status_code} | {response.text}")
        except Exception as e:
            logger.error(f"ZADARMA API REQUEST FAILED: {str(e)}")


@app.get("/webhook/zadarma")
def verify_webhook(zd_echo: str = Query(None)):
    if zd_echo:
        return Response(content=zd_echo, media_type="text/plain")
    return Response(content="OK", media_type="text/plain")


@app.post("/webhook/zadarma")
async def handle_zadarma_webhook(request: Request):
    form_data = await request.form()
    payload = {key: value for key, value in form_data.items()}

    logger.info(f"ZADARMA RAW PAYLOAD: {payload}")

    event = payload.get("event")
    call_id = payload.get("pbx_call_id") or payload.get("call_id_with_prefix") or payload.get("call_id")
    caller = payload.get("caller_id")
    called = payload.get("called_did") or payload.get("called_id")
    status = payload.get("disposition") or payload.get("status")
    duration = payload.get("duration")
    link = payload.get("rec_link") or payload.get("pbs_record_link")
    text = payload.get("text")
    language = payload.get("language")
    call_id_with_rec = payload.get("call_id_with_rec")


    logger.info(
        f"ZADARMA PARSED -> Event: {event} | ID: {call_id} | Caller: {caller} | "
        f"Called: {called} | Status: {status} | Duration: {duration}s | "
        f"Link: {link} | Language: {language} | Text: {text}"
    )

    if event == "NOTIFY_RECORD" and call_id_with_rec:
        await fetch_call_recording_data(call_id_with_rec)

    return Response(content="OK", media_type="text/plain")