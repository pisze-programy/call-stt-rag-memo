from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CallerSession(BaseModel):
    email_address: Optional[str] = None
    caller_id: str
    updated_at: Optional[datetime] = None
