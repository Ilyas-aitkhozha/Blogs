from datetime import datetime
from pydantic import BaseModel, ConfigDict

class WorkerTeamMemberCreate(BaseModel):
    user_id: int
    model_config = ConfigDict(from_attributes=True)