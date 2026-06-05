import base64
import hashlib
import hmac
import io
import logging
import os
import sys
from urllib.parse import urlencode, quote

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
    # AUTH https://zadarma.com/en/support/api/#intro_authorization
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


async def zadarma_request(method: str, api_method: str, params: dict):
    params_str = urlencode(sorted(params.items()), quote_via=quote, safe="")
    auth_header = generate_auth_header(
        api_method,
        params_str,
        os.getenv("ZADARMA_SECRET"),
        os.getenv("ZADARMA_KEY")
    )

    url = f"{os.getenv('ZADARMA_API_URL')}{api_method}"
    headers = {"Authorization": auth_header, "Accept": "application/json"}

    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, params=params, headers=headers)
        return response


async def fetch_call_recording_data(call_id_with_rec: str):
    # GET https://zadarma.com/en/support/api/#api_pbx_record_request
    response = await zadarma_request("GET", "/v1/pbx/record/request/", {"call_id": call_id_with_rec})
    if response.status_code == 200:
        return response.json()
    logger.error(f"FETCH FAILED: {response.status_code} | {response.text}")
    return None


async def delete_recording_data(pbx_call_id: str) -> bool:
    # DELETE https://zadarma.com/en/support/api/#api_pbx_delete_record_request
    response = await zadarma_request("DELETE", "/v1/pbx/record/request/", {"pbx_call_id": pbx_call_id})
    if response.status_code == 200 and response.json().get("status") == "success":
        logger.info(f"CLEANUP SUCCESS | Deleted: {pbx_call_id}")
        return True
    logger.error(f"CLEANUP FAILED: {response.status_code} | {response.text}")
    return False

def save_to_vector_db(caller_phone: str, text: str) -> bool:
    logger.info(f"save_to_vector_db: {caller_phone}, {text}")
    return True


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
    # unique ID of the call with the call recording
    call_id_with_rec = payload.get("call_id_with_rec")
    call_id = payload.get("call_id")
    pbx_call_id = payload.get("pbx_call_id")
    caller_phone = payload.get("caller_id")

    # https://zadarma.com/en/support/api/#api_webhook_notify_record
    if event == "NOTIFY_RECORD" and call_id_with_rec:
        data = await fetch_call_recording_data(call_id_with_rec)

        if data and "link" in data:
            text = await process_recording_to_text(data["link"], call_id_with_rec)

            if text:
                save_to_vector_db(caller_phone, text)
                logger.info(f"ZADARMA pbx_call_id: {pbx_call_id}")
                logger.info(f"ZADARMA call_id_with_rec: {call_id_with_rec}")
                await delete_recording_data(pbx_call_id)
        else:
            logger.error(f"ABORTED | No download link available for call: {call_id_with_rec}")

    return Response(content="OK", media_type="text/plain")