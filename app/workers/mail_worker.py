import asyncio

from dotenv import load_dotenv

from app.database.caller_operations import get_caller
from app.modules.mailer import Mailer

load_dotenv()

from app.modules.logger import logger
from app.workers.kafka_worker import run_worker


mailer = Mailer()

async def handle_mail_event(payload):
    try:
        caller_id = payload.get("caller_id")
        subject = payload.get("subject")
        body = payload.get("body")

        if not caller_id or not subject or not body:
            raise ValueError(f"Incomplete payload: {payload}")

        caller = await get_caller(caller_id)

        if not caller or not caller.email_address:
            logger.warning(f"No valid email found for {caller_id}")
            return

        email_address = caller.email_address

        if not email_address:
            logger.warning(f"No email bound for {caller_id}, skipping")
            return

        success = mailer.send(email_address, subject, body)

        if not success:
            raise RuntimeError(f"Mailer failed to send email to {email_address}")
    except Exception as e:
        logger.error(f"Error sending email via ${e}", exc_info=True)

    logger.info(f"Received mail event: {payload}")

if __name__ == "__main__":
    asyncio.run(run_worker("mail", "notia-mail-group", handle_mail_event))