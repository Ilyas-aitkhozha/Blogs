from pydantic import BaseModel, EmailStr, Field
from typing import List, Annotated
from enum import Enum

class UserRole(str, Enum):
    user = "user"
    admin = "admin"

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class ShowUser(UserBase):
    id: int
    role: UserRole

    class Config:
        from_attributes = True

class UserWithTickets(ShowUser):
    tickets_created: Annotated[List["TicketOut"], Field(default_factory=list)]
    tickets_assigned: Annotated[List["TicketOut"], Field(default_factory=list)]

    class Config:
        from_attributes = True

from .ticket import TicketOut
UserWithTickets.model_rebuild()
