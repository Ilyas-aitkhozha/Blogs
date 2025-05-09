from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

# brief scheme
class TeamBrief(BaseModel):
    id: int
    name: str
    code: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class ProjectWorkerTeamBase(BaseModel):
    project_id: int
    team_id: int
    assigned_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProjectWorkerTeamRead(ProjectWorkerTeamBase):
    team: TeamBrief

class ProjectWithWorkers(BaseModel):
    id: int
    name: str
    worker_team_links: List[ProjectWorkerTeamRead]
    worker_teams: List[TeamBrief]
    model_config = ConfigDict(from_attributes=True)