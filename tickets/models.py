from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, DateTime, Enum as SqlEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base
from enum import Enum

class UserRole(str, Enum):
    user = "user"
    admin = "admin"

class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"

class SessionRecord(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete = "CASCADE"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="sessions")


class User(Base):
    __tablename__ = 'users'
    is_available = Column(Boolean, default=True)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(SqlEnum(UserRole, native_enum=False), default=UserRole.user)
    tickets_created = relationship("Ticket", back_populates="creator", foreign_keys="Ticket.created_by",cascade="all, delete-orphan")
    tickets_assigned = relationship("Ticket", back_populates="assignee", foreign_keys="Ticket.assigned_to")
    sessions = relationship("SessionRecord", back_populates="user",cascade="all, delete-orphan")

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(SqlEnum(TicketStatus, native_enum=False), default=TicketStatus.open)
    created_by = Column(Integer, ForeignKey("users.id", ondelete = "CASCADE"))
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete = "SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),onupdate=lambda: datetime.now(timezone.utc))

    creator = relationship("User", back_populates="tickets_created", foreign_keys=[created_by])
    assignee = relationship("User", back_populates="tickets_assigned", foreign_keys=[assigned_to])

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String)
    content = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    session = relationship("SessionRecord")
