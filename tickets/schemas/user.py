from pydantic import BaseModel, Field
from typing import List
from typing_extensions import Annotated
from enum import Enum
from typing import TYPE_CHECKING
from tickets.schemas.team import TeamOut

if TYPE_CHECKING:
    from tickets.schemas.ticket import TicketOut


class UserRole(str, Enum):
    user = "user"
    admin = "admin"

class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    password: str

class ShowUser(UserBase):
    id: int
    role: UserRole
    is_available: bool
    teams: list[TeamOut]

    class Config:
        from_attributes = True

class UserWithTickets(ShowUser):
    tickets_created: Annotated[List["TicketOut"], Field(default_factory=list)]
    tickets_assigned: Annotated[List["TicketOut"], Field(default_factory=list)]

    class Config:
        from_attributes = True
