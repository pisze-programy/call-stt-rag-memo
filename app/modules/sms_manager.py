import os

from openai import AsyncOpenAI

from app.models.Interpretation import Interpretation
from app.models.action import ActionInterpretation

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def classify_sms_intent(text: str) -> ActionInterpretation:
    system_prompt = """
    Analyze the user's SMS and classify it into one of these intents:
    1. BIND_EMAIL: If the text contains a valid email. Provide the email.
    2. QUERY_NOTES: The user is explicitly asking to retrieve, search, or summarize existing notes.
    3. SAVE_NOTE: The user is expressing a thought, stating a fact, describing an event, or saving an idea.
    4. REJECT: Only if the text is completely empty or makes no sense.

    Return JSON matching exactly this schema: 
    {"intent": "BIND_EMAIL" | "QUERY_NOTES" | "SAVE_NOTE" | "REJECT", "email": "string" | null, "note_content": "string" | null, "query": "string" | null}
    """

    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
    )

    return Interpretation.model_validate_json(response.choices[0].message.content)