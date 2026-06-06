from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class CallStatus(str, Enum):
    INIT = "init"
    END = "end"

class CallSession(BaseModel):
    pbx_call_id: str
    caller_id: str
    called_did: str
    start_time: Optional[datetime]
    duration: Optional[int] = None
    status: CallStatus = CallStatus.INIT
    is_recorded: bool = False
    notes: Optional[str] = None
    audio_path: Optional[str] = None