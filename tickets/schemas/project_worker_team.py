from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional
from tickets.schemas.team import TeamBriefInfo

class ProjectWorkerTeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ProjectWorkerTeamCreate(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)

class ProjectWorkerTeamRead(ProjectWorkerTeamBase):
    id: int
    project_id: int
    team_id: int
    assigned_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectWithWorkers(BaseModel):
    id: int
    name: str
    worker_team_links: List[ProjectWorkerTeamRead]
    model_config = ConfigDict(from_attributes=True)
