from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.webhooks import router as webhook_router
from app.database.mongodb import db

load_dotenv()

app = FastAPI()
app.include_router(webhook_router)

client = db.connect_to_database("mongodb://localhost:27017", "memo_store")
