from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime
from blog.schemas import user


class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"

class TicketBase(BaseModel):
    title: str
    description: str

class TicketCreate(TicketBase):
    assigned_to_name: Optional[str] = None # for names

class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    assigned_to: Optional[int] = None

class TicketOut(TicketBase):
    id: int
    status: TicketStatus
    created_by: user.ShowUser
    assigned_to: Optional[user.ShowUser]
    created_at: datetime

    class Config:
        from_attributes = True
