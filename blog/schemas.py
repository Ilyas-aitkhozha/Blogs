from pydantic import BaseModel
from typing import List, Optional
#in pydantic, we call it not model but schemas

class BlogBase(BaseModel):
    title: str
    body: str
class Blog(BlogBase):
    id: int
    class Config():
        from_attributes = True

class User(BaseModel):
    name: str
    email: str
    password: str

class ShowUser(BaseModel):
    name: str
    email: str
    blogs: List[Blog] # listing all blogs that user have
    class Config():
        from_attributes = True

class Showblog(BaseModel):
    title: str
    body: str
    creator: ShowUser
    class Config():
        from_attributes = True
