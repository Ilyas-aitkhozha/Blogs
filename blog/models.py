from sqlalchemy import Integer, String, Column, ForeignKey
from .database import Base
from sqlalchemy.orm import relationship

#call module for sqlalchemy

class Blog(Base):
    __tablename__ = 'blogs'
    id = Column(Integer, primary_key=True, index = True)
    title = Column(String)
    body = Column(String)
    user_id = Column(Integer, ForeignKey("users.id")) # made relations with blogs and user
    creator = relationship("User", back_populates="blogs")

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index = True)
    name = Column(String)
    email = Column(String)
    password = Column(String)

    blogs = relationship("Blog", back_populates="creator")

