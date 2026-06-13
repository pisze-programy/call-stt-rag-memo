from datetime import datetime

from app.database.mongodb import db
from app.models.caller import CallerSession


async def upsert_caller(caller_id: str):
    return await db.callers.find_one_and_update(
        {"caller_id": caller_id},
        {"$setOnInsert": {"caller_id": caller_id, "email_address": None}},
        upsert=True,
        return_document=True
    )

async def get_caller(caller_id: str) -> dict:
    return await db.callers.find_one({"caller_id": caller_id})

async def update_email(caller_id: str, email: str) -> bool:
    result = await db.callers.update_one(
        {"caller_id": caller_id},
        {"$set": {"email_address": email, "updated_at": datetime.now()}},
    )
    return result.modified_count > 0

async def update_calendar_id(caller_id: str, calendar_id: str) -> bool:
    result = await db.callers.update_one(
        {"caller_id": caller_id},
        {"$set": {"calendar_id": calendar_id, "updated_at": datetime.now()}},
    )
    return result.modified_count > 0