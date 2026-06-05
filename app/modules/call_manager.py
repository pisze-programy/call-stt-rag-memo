from app.database.mongodb import db
from app.modules.logger import logger

async def get_collection(name: str):
    return db.db[name]

async def upsert_call(pbx_call_id: str, payload: dict):
    collection = await get_collection("calls")
    logger.info(f"Upserting call {pbx_call_id}")