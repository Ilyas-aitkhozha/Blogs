from pydantic import BaseModel, Field
from typing import List
from pydantic import ConfigDict
from typing_extensions import Annotated
from typing import TYPE_CHECKING, Optional
from tickets.schemas.team import TeamWithProjects
from datetime import datetime
from .project import ProjectMembership
from ..enums import *

if TYPE_CHECKING:
    from tickets.schemas.ticket import TicketOut


#base, parent
class UserBase(BaseModel):
    name: str
#creating with name and password
class UserCreate(UserBase):
    password: str

#showing user info
class ShowUser(UserBase):
    id: int
    email: Optional[str] = None
    is_available: bool
    teams: List[TeamWithProjects]
    model_config = ConfigDict(from_attributes=True)

class UserBrief(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)
#giving info about users and also ticket that he created
class UserWithTickets(ShowUser):
    tickets_created: Annotated[List["TicketOut"], Field(default_factory=list)]
    tickets_assigned: Annotated[List["TicketOut"], Field(default_factory=list)]

    model_config = ConfigDict(from_attributes=True,populate_by_name=True)

class UserAvailabilityOut(BaseModel):
    id: int
    is_available: bool
    model_config = ConfigDict(from_attributes=True)

class UserInTeamWithProjects(BaseModel):
    user: UserBrief
    role: TeamRole
    joined_at: datetime
    projects: List[ProjectMembership]
    model_config = ConfigDict(from_attributes=True)
