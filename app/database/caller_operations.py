from app.database.mongodb import db


async def upsert_caller(caller_id: str):
    return await db.callers.find_one_and_update(
        {"caller_id": caller_id},
        {"$setOnInsert": {"caller_id": caller_id, "email": None}},
        upsert=True,
        return_document=True
    )

async def get_caller(caller_id: str):
    return await db.callers.find_one({"caller_id": caller_id})

async def update_email(caller_id: str, email: str) -> bool:
    result = await db.callers.update_one(
        {"caller_id": caller_id},
        {"$set": {"email": email}}
    )
    return result.modified_count > 0