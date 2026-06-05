import base64
import hashlib
import hmac
import os
from urllib.parse import urlencode, quote

import httpx

from app.modules.logger import logger


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