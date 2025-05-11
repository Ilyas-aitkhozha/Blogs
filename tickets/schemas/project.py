from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional
from ..enums import ProjectRole

class ProjectBase(BaseModel):
    name: str
    description: Optional[str]

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdateWorker(BaseModel):
    worker_team_id: Optional[int]
    model_config = ConfigDict(from_attributes=True)
class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    team_id: int
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectMembership(BaseModel):
    project: ProjectOut
    role: ProjectRole
    joined_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProjectBrief(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)