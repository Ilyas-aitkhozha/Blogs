from sqlalchemy import Integer, String, Column, ForeignKey, DateTime
from .database import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class SessionRecord(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Blog(Base):
    __tablename__ = 'blogs'
    id       = Column(Integer, primary_key=True, index=True)
    title    = Column(String)
    body     = Column(String)
    user_id  = Column(Integer, ForeignKey("users.id"))
    creator  = relationship("User", back_populates="blogs")   # points to User.blogs

class User(Base):
    __tablename__ = 'users'
    id       = Column(Integer, primary_key=True, index=True)
    name     = Column(String)
    email    = Column(String)
    password = Column(String)

    # ← You must add this line back:
    blogs    = relationship("Blog", back_populates="creator")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id         = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    role       = Column(String)
    content    = Column(String)
    timestamp  = Column(DateTime, default=datetime.utcnow)
