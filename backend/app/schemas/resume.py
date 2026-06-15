from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ResumeCreate(BaseModel):
    title: str
    template: str = "modern"
    content: dict = {}

class ResumeUpdate(BaseModel):
    title: str
    content: dict

class ResumeResponse(BaseModel):
    id: int
    user_id: int
    title: str
    template: str
    content: dict
    created_at: datetime

    class Config:
        from_attributes = True