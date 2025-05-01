from pydantic import BaseModel
from pydantic import ConfigDict
from typing import Optional
from enum import Enum
from datetime import datetime
from tickets.schemas import user

class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"

class TicketBase(BaseModel):
    title: str
    description: str

class TicketCreate(TicketBase):
    assigned_to_name: Optional[str] = None

class TicketStatusUpdate(BaseModel):
    status: TicketStatus

class TicketAssigneeUpdate(BaseModel):
    assigned_to: int

class TicketOut(TicketBase):
    id: int
    status: TicketStatus
    creator: user.ShowUser
    assignee: Optional[user.ShowUser]
    team_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
