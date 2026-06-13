from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel

from app.models.Interpretation import Interpretation


class CallStatus(str, Enum):
    INIT = "init"
    END = "end"

class CallSession(BaseModel):
    pbx_call_id: str
    internal: str
    email_address: Optional[str] = None
    caller_id: str
    called_did: str
    start_time: Optional[datetime]
    duration: Optional[int] = None
    status: CallStatus = CallStatus.INIT
    is_recorded: bool = False
    audio_path: Optional[str] = None
    transcription: Optional[str] = None
    interpretation: Optional[Interpretation] = None
    embedding: Optional[List[float]] = None
    updated_at: Optional[datetime] = None
