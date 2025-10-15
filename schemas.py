from typing import List, Optional
from pydantic import BaseModel


class MeetingCreate(BaseModel):
    filename: str


class MeetingOut(BaseModel):
    id: int
    filename: str
    transcript: Optional[str]
    summary: Optional[str]
    decisions: Optional[List[str]]
    action_items: Optional[List[str]]

    class Config:
        from_attributes = True


