from pydantic import BaseModel
from typing import List, Optional, Literal


class Activity(BaseModel):
    verb: Optional[str] = None
    object: Optional[str] = None
    outcome: Optional[str] = None


class Person(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None


class Location(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None


class TimeReference(BaseModel):
    raw: Optional[str] = None
    resolved: Optional[str] = None
    relative: Optional[Literal["past", "present", "future", None]] = None


class Interpretation(BaseModel):
    note_type: Literal["event", "meeting", "person", "place", "task", "fact", "other", "unknown"]
    activity: Optional[Activity] = None
    people: List[Person] = []
    locations: List[Location] = []
    time_reference: Optional[TimeReference] = None
    sentiment: Optional[str] = None
    entities: List[str] = []
    summary: str
    vector_string: str