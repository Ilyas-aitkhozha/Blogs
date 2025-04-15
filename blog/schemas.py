from pydantic import BaseModel

#in pydantic, we call it not model but schemas

class Blog(BaseModel):
    title: str
    body: str

class Showblog(BaseModel):
    body: str
    class Config():
        from_attributes = True

class User(BaseModel):
    name: str
    email: str
    password: str
class ShowUser(BaseModel):
    name: str
    email: str
    password: str
    class Config():
        from_attributes = True