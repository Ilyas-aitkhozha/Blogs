from pydantic import BaseModel, EmailStr
from typing import List, Optional

class Blog(BaseModel):
    title: str
    body: str

    class Config:
        from_attributes = True

class User(BaseModel):
    name: str
    email: str
    password: str

class ShowUser(BaseModel):
    name: str
    email: str
    blogs: List[Blog]

    class Config:
        from_attributes = True

class Showblog(Blog):
    creator: Optional['ShowUser']  # forward reference

    class Config:
        from_attributes = True

class Login(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
class ChatResponse(BaseModel):
    reply: str
    session_id: str


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        orm_mode = True

Showblog.update_forward_refs()
