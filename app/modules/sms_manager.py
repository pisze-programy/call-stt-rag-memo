import os

from openai import AsyncOpenAI

from app.models.action import ActionInterpretation

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def classify_sms_intent(text: str) -> ActionInterpretation:
    system_prompt = """
    You are an intent classifier for an SMS-based personal note system.
    
    ## The Core Question:
    Does this message NEED a response from the system, or is the user just CAPTURING a thought?
    
    ## Intent Definitions:
    
    ### SAVE_NOTE — User is capturing information
    The user is the SOURCE of information. They are recording something.
    Signals:
    - Describes an event, meeting, observation ("Spotkałem X", "Byłem na...")  
    - Contains a question but ALSO contains the user's own answer or reflection
    - Thinking out loud ("Nie pamiętam ale chyba...", "Wydaje mi się że...")
    - Stream of consciousness with embedded rhetorical questions
    - The message is self-contained — it doesn't need a system reply to make sense
    
    ### QUERY_NOTES — User wants information FROM the system  
    The user is the RECIPIENT of information. They expect an answer.
    Signals:
    - Standalone question with no self-provided answer
    - Explicit recall request
    - The message cannot stand alone — it REQUIRES a system response
    
    ### BIND_EMAIL — message contains valid email address
    ### REJECT — empty or completely unintelligible noise only
    
    ## Decision Tree:
    1. Contains email? → BIND_EMAIL
    2. Is the user answering their own question, or thinking out loud? → SAVE_NOTE
    3. Does the message require a system response to be useful? → QUERY_NOTES
    4. Truly unintelligible? → REJECT

    ## Output Format (strict JSON, no markdown):
    {"intent": "BIND_EMAIL" | "QUERY_NOTES" | "SAVE_NOTE" | "REJECT", "email": "string | null"}

    """

    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
    )

    return ActionInterpretation.model_validate_json(response.choices[0].message.content)