from pydantic import BaseModel, EmailStr, Field
from typing import List
from typing_extensions import Annotated
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from blog.schemas.ticket import TicketOut


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
    is_available: bool

    class Config:
        from_attributes = True

class UserWithTickets(ShowUser):
    tickets_created: Annotated[List["TicketOut"], Field(default_factory=list)]
    tickets_assigned: Annotated[List["TicketOut"], Field(default_factory=list)]

    class Config:
        from_attributes = True
