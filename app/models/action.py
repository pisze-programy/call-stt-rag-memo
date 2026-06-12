from typing import Literal, Optional

from pydantic import EmailStr, BaseModel


class ActionInterpretation(BaseModel):
    intent: Literal["SAVE_NOTE", "BIND_EMAIL", "UNBIND_EMAIL", "QUERY_NOTES", "REJECT"]
    email: Optional[EmailStr] = None
    note_content: Optional[str] = None
    query: Optional[str] = None