from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from tickets.schemas.ticket import TicketOut

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    ticket: Optional[TicketOut] = None

    class Config:
        from_attributes = True

class ChatMessageOut(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True
