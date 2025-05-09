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