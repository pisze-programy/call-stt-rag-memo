from fastapi import Query, Request, Response, APIRouter

from app.modules.kafka_client import get_producer
from app.modules.logger import logger

router = APIRouter()


@router.get("/webhook/zadarma")
def verify_webhook(zd_echo: str = Query(None)):
    if zd_echo:
        return Response(content=zd_echo, media_type="text/plain")
    return Response(content="OK", media_type="text/plain")


@router.post("/webhook/zadarma")
async def handle_zadarma_webhook(request: Request):
    # https://zadarma.com/en/support/api/#api_webhook_notify_record
    form_data = await request.form()
    payload = {key: value for key, value in form_data.items()}

    logger.info(f"ZADARMA RAW PAYLOAD: {payload}")

    event_type = payload.get("event")

    topic_map = {
        "NOTIFY_INTERNAL": "zadarma_start",
        "NOTIFY_END": "zadarma_end",
        "NOTIFY_RECORD": "zadarma_record",
        "SMS": 'zadarma_sms'
    }

    topic = topic_map.get(event_type)
    if topic:
        get_producer().send(topic, value=payload)

    return Response(content="OK", media_type="text/plain")