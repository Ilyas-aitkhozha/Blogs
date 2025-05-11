from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class WorkerTeamBase(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)

class WorkerTeamCreate(WorkerTeamBase):
    pass

class WorkerTeamRead(WorkerTeamBase):
    id: int
    created_at: datetime
    # список проектов, которые обслуживает команда
    projects: List[int] = []  # можно заменить на List[ProjectBrief] при наличии
    model_config = ConfigDict(from_attributes=True)