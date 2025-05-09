from pydantic import BaseModel
from pydantic import ConfigDict
from typing import Optional
from datetime import datetime
from tickets.schemas import user
from ..enums import *



#base, parent
class TicketBase(BaseModel):
    title: str
    description: str

class TicketCreate(TicketBase):
    type: TicketType
    assigned_to_name: Optional[str] = None
    priority: Optional[TicketPriority] = TicketPriority.medium

class TicketStatusUpdate(BaseModel):
    status: TicketStatus

class TicketFeedbackUpdate(BaseModel):
    feedback: Optional[str] = None
    confirmed: bool

class TicketAssigneeUpdate(BaseModel):
    assigned_to: int
#we can create tickets only in projects, so i removed team_id
class TicketOut(TicketBase):
    id: int
    type: TicketType
    status: TicketStatus
    creator: user.UserBrief
    assignee: Optional[user.UserBrief]
    created_at: datetime
    priority: TicketPriority
    confirmed: bool
    feedback: Optional[str]
    model_config = ConfigDict(from_attributes=True)
