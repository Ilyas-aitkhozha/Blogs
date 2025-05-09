from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# brief scheme
class TeamBrief(BaseModel):
    id: int
    name: str
    code: Optional[str]
    model_config = ConfigDict(from_attributes=True)