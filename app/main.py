import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.webhooks import router as webhook_router
from app.api.health import router as health_router
from app.database.mongodb import db

load_dotenv()

@asynccontextmanager
async def lifespan(_: FastAPI):
    await db.connect(os.getenv("MONGO_URI"), "memo_store")
    yield
    await db.close()

app = FastAPI(lifespan=lifespan)
app.include_router(webhook_router)
app.include_router(health_router)
