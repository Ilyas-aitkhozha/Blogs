# schemas/chat.py

from pydantic import BaseModel
from datetime import datetime

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    session_id: str

class ChatMessageOut(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True
