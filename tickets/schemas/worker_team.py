from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, Optional, Annotated
from tickets.schemas.project import ProjectBrief

class WorkerTeamBase(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)

class WorkerTeamCreate(WorkerTeamBase):
    pass

class WorkerTeamUpdate(BaseModel):
    name: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class WorkerTeamRead(WorkerTeamBase):
    id: int
    created_at: datetime
    projects: Annotated[List[ProjectBrief], Field(default_factory=list)]
    model_config = ConfigDict(from_attributes=True)

class WorkerTeamBrief(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)
