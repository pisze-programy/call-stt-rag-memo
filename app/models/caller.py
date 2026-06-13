from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CallerSession(BaseModel):
    caller_id: str
    email_address: Optional[str] = None
    calendar_id: Optional[str]
    updated_at: Optional[datetime] = None
