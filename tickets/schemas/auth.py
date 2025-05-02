from pydantic import BaseModel
from typing import Optional, Literal

class Login(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"

class TokenData(BaseModel):
    sub: Optional[str] = None
