from pydantic import BaseModel
from datetime import datetime

class TeamCreate(BaseModel):
    name: str

class TeamOut(BaseModel):
    id: int
    name: str
    code: str
    created_at: datetime

    class Config:
        from_attributes = True


class JoinTeam(BaseModel):
    code: str