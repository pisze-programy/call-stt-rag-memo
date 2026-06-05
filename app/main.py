import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.webhooks import router as webhook_router
from app.database.mongodb import db

load_dotenv()

app = FastAPI()
app.include_router(webhook_router)

MONGO_URI = os.getenv("MONGO_URI")
client = db.connect_to_database(MONGO_URI, "memo_store")
