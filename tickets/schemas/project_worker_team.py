from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List
from tickets.schemas.team import TeamBriefInfo

class ProjectWorkerTeamBase(BaseModel):
    team_id: int
    assigned_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProjectWorkerTeamRead(ProjectWorkerTeamBase):
    project_id: int
    team: TeamBriefInfo
    model_config = ConfigDict(from_attributes=True)

class ProjectWithWorkers(BaseModel):
    id: int
    name: str
    worker_team_links: List[ProjectWorkerTeamRead]
    model_config = ConfigDict(from_attributes=True)
