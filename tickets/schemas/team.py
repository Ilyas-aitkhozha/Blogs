from pydantic import BaseModel
from datetime import datetime
from pydantic import ConfigDict


class TeamCreate(BaseModel):
    name: str

class TeamOut(BaseModel):
    id: int
    name: str
    code: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class JoinTeam(BaseModel):
    code: str