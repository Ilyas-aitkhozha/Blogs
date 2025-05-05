from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class ProjectBase(BaseModel):
    name: str
    description: Optional[str]
    team_id: int

class ProjectCreate(ProjectBase):
    pass

class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    team_id: int
    created_by: int
    created_at: datetime
    worker_team: List[int]

    model_config = ConfigDict(from_attributes=True)