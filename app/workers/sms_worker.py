import asyncio
import json

from dotenv import load_dotenv

from app.database.caller_operations import upsert_caller, update_email
from app.modules.memory_manager import save_to_vector_db, interpret_input, embed_text, normalize_phone_smart, \
    notify_user, refine_search_query, perform_vector_search
from app.modules.sms_manager import classify_sms_intent

load_dotenv()

from app.modules.logger import logger

from app.workers.kafka_worker import run_worker


async def handle_save_note(phone, text):
    try:
        interpretation = await interpret_input(text)
        embedding = await embed_text(text)

        await save_to_vector_db(
            phone,
            text,
            embedding,
            interpretation
        )

        await notify_user(
            phone,
            "Note Saved",
            f"Your note has been successfully saved:\n\n{text}"
        )
    except Exception as e:
        logger.error(f"Note Interpretation error: {str(e)}")
        await notify_user(phone, "Note Save Error", f"Failed to process your note: {text}")
        return None

async def handle_bind_email(caller_id, email):
    if email is None:
        return None
    await upsert_caller(caller_id)
    await update_email(caller_id, email)
    await notify_user(caller_id, "Email Bound", f"Your email {email} has been successfully registered.")
    return None

async def handle_query_notes(caller_id, text):
    interpretation = await refine_search_query(text)
    answer = await perform_vector_search(caller_id, interpretation)

    logger.info(f"Query result: {answer}")
    await notify_user(caller_id, "Query Result", answer)
    return None

async def handle_sms(payload: dict):
    await asyncio.sleep(0)
    logger.info(f"Received message: {payload}")
    result = json.loads(payload.get('result', '{}'))
    text = result.get('text', '')
    caller_id = result.get('caller_id')
    phone = normalize_phone_smart(caller_id)

    if (phone is None) or (text is None):
        logger.info(f"SMS ignored or invalid: {text}")
        return None

    if not text or not text.strip():
        await notify_user(phone, "Processing Error", "Received an empty message. Please provide valid content.")
        return {"intent": "REJECT", "email": None, "note_content": None, "query": None}

    try:
        result = await classify_sms_intent(text)
        intent = result.intent
        email = result.email

        logger.info(f"classify response: {text} {phone} {result}")

        if intent == 'SAVE_NOTE':
            await handle_save_note(phone, text)
        elif intent == 'BIND_EMAIL':
            await handle_bind_email(phone, email)
        elif intent == 'QUERY_NOTES':
            await handle_query_notes(phone, text)
        else:
            logger.info(f"SMS ignored or invalid: {text}")
    except (json.JSONDecodeError, KeyError, AssertionError) as e:
        logger.error(f"Invalid LLM response: {text}, error: {e}")


if __name__ == "__main__":
    asyncio.run(run_worker("zadarma_sms", "sms_processing_group", handle_sms))