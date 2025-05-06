from pydantic import BaseModel, Field
from typing import Optional,List
from datetime import datetime
from pydantic import ConfigDict
from ..enums import TeamRole
from .project import ProjectMembership

class TeamCreate(BaseModel):
    name: str

class TeamOut(BaseModel):
    id: int
    name: str
    code: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TeamBriefInfo(BaseModel):
    name:str
    code:str
    model_config = ConfigDict(from_attributes=True)

class TeamMembership(BaseModel):
    team: TeamOut
    role: TeamRole
    joined_at: datetime
    model_config = ConfigDict(from_attributes=True)

class JoinTeam(BaseModel):
    code: str

class TeamWithProjects(BaseModel):
    team: TeamOut
    role: TeamRole
    joined_at: datetime
    projects: List[ProjectMembership]
    model_config = ConfigDict(from_attributes=True)