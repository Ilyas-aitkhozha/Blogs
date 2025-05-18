from datetime import datetime
from pydantic import BaseModel, ConfigDict

class WorkerTeamMemberCreate(BaseModel):
    user_id: int
    model_config = ConfigDict(from_attributes=True)

class WorkerTeamMemberRead(BaseModel):
    user_id: int
    worker_team_id: int
    joined_at: datetime
    model_config = ConfigDict(from_attributes=True)