from pydantic import BaseModel, Field
from typing import List
from typing_extensions import Annotated
from enum import Enum
from typing import TYPE_CHECKING
from tickets.schemas.team import TeamOut

if TYPE_CHECKING:
    from tickets.schemas.ticket import TicketOut

#enumki
class UserRole(str, Enum):
    user = "user"
    admin = "admin"
#base, parent
class UserBase(BaseModel):
    name: str
#creating with name and password
class UserCreate(UserBase):
    password: str

#showing user info
class ShowUser(UserBase):
    id: int
    role: UserRole
    is_available: bool
    teams: list[TeamOut]

    class Config:
        from_attributes = True
#giving info about users and also ticket that he created
class UserWithTickets(ShowUser):
    tickets_created: Annotated[List["TicketOut"], Field(default_factory=list)]
    tickets_assigned: Annotated[List["TicketOut"], Field(default_factory=list)]

    class Config:
        from_attributes = True
