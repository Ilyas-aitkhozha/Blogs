from datetime import datetime
from pydantic import BaseModel, ConfigDict

class WorkerTeamCreate(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)

class WorkerTeamRead(BaseModel):
    id: int
    team_id: int
    name: str
    created_at: datetime
    admin_id: int

    model_config = ConfigDict(from_attributes=True)

class WorkerTeamBrief(BaseModel):
    id: int
    name: str
    team_id: int
    model_config = ConfigDict(from_attributes=True)