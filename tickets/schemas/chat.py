from pydantic import BaseModel
from datetime import datetime
from pydantic import ConfigDict
from typing import Optional
from tickets.schemas.ticket import TicketOut

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    ticket: Optional[TicketOut] = None
    model_config = ConfigDict(from_attributes=True)


class ChatMessageOut(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
