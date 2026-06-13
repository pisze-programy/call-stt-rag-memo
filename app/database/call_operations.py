from datetime import datetime

from app.database.mongodb import db
from app.models.call import CallStatus, CallSession


async def initialize_call(pbx_call_id: str, caller_id: str, called_did: str, call_start: str, internal: str):
    await db.calls.update_one(
        {"pbx_call_id": pbx_call_id},
        {
            "$set": {
                "caller_id": caller_id,
                "internal": internal,
                "called_did": called_did,
                "start_time": call_start,
                "status": CallStatus.INIT
            }
        },
        upsert=True
    )

async def finalize_call(pbx_call_id: str, duration: int, is_recorded: bool):
    await db.calls.update_one(
        {"pbx_call_id": pbx_call_id},
        {
            "$set": {
                "duration": duration,
                "is_recorded": is_recorded,
                "status": CallStatus.END,
                "updated_at": datetime.now()
            }
        }
    )

async def update_call_recording_link(pbx_call_id: str, audio_path: str):
    await db.calls.update_one(
        {"pbx_call_id": pbx_call_id},
        {
            "$set": {
                "audio_path": audio_path,
                "updated_at": datetime.now()
            }
        }
    )

async def update_call_transcription(pbx_call_id: str, transcription: str, interpretation: str):
    await db.calls.update_one(
        {"pbx_call_id": pbx_call_id},
        {
            "$set": {
                "transcription": transcription,
                "updated_at": datetime.now(),
                "interpretation": interpretation
            }}
    )

async def get_call_by_pbx_id(pbx_call_id: str) -> CallSession:
    return await db.calls.find_one({"pbx_call_id": pbx_call_id})
