import asyncio

from dotenv import load_dotenv

load_dotenv()

from app.modules.logger import logger
from app.workers.kafka_worker import run_worker


async def handle_mail_event(payload):
    logger.info(f"Received mail event: {payload}")

if __name__ == "__main__":
    asyncio.run(run_worker("mail", "notia-mail-group", handle_mail_event))