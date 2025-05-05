from sqlalchemy import Column, Integer, Boolean, String, ForeignKey,Text, DateTime, Enum as SqlEnum
from sqlalchemy.orm import relationship
import random, string
from datetime import datetime, timezone
from .database import Base
from enum import Enum

#enumki
class UserRole(str, Enum):
    user = "user"
    worker = "worker"
    admin = "admin"
    superadmin = "superadmin"

class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"

class TicketPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

#helper
def _generate_team_code(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

#db for teams, user,tickets
class ProjectWorkerTeam(Base):
    __tablename__ = "project_worker_teams"
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    worker_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

class UserTeam(Base):
    #this is  middle table, that helps with relationship many-to-many (user and team)
    __tablename__ = "user_teams"
    user_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    team_id   = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="user_teams")
    team = relationship("Team", back_populates="user_teams")

class Team(Base):
    __tablename__ = "teams"
    #all the users and tickets are created in side team
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String, nullable=False)
    code       = Column(String, unique=True, index=True, default=_generate_team_code)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_teams = relationship("UserTeam", back_populates="team", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="team")
    members = relationship("User", secondary="user_teams", back_populates="teams", overlaps='user_teams')
    tickets = relationship("Ticket", back_populates="team", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    password = Column(String, nullable=False)
    role = Column(SqlEnum(UserRole, native_enum=False), default=UserRole.user)# superadmin, admin, worker, user
    is_available = Column(Boolean, default=True)
    user_teams = relationship("UserTeam", back_populates="user", cascade="all, delete-orphan", overlaps="teams")
    teams = relationship("Team", secondary="user_teams", back_populates="members", overlaps="user_teams")
    tickets_created = relationship("Ticket", back_populates="creator", foreign_keys="Ticket.created_by", cascade="all, delete-orphan")
    tickets_assigned = relationship("Ticket", back_populates="assignee", foreign_keys="Ticket.assigned_to")
    sessions = relationship("SessionRecord", back_populates="user", cascade="all, delete-orphan")
    assigned_projects = relationship(
        "Project",
        secondary=ProjectWorkerTeam.__tablename__,
        back_populates="worker_team"
    )

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(SqlEnum(TicketStatus, native_enum=False), default=TicketStatus.open)
    priority = Column(SqlEnum(TicketPriority, native_enum=False), default=TicketPriority.medium)
    confirmed = Column(Boolean, default=False)
    feedback = Column(String, nullable=True)
    created_by  = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    team_id     = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"))
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    accepted_at = Column(DateTime, nullable=True)
    closed_at   = Column(DateTime, nullable=True)
    updated_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    project = relationship("Project", back_populates="tickets")
    creator  = relationship("User", back_populates="tickets_created", foreign_keys=[created_by])
    assignee = relationship("User", back_populates="tickets_assigned", foreign_keys=[assigned_to])
    team     = relationship("Team", back_populates="tickets")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="projects")
    creator = relationship("User")
    tickets = relationship("Ticket", back_populates="project", cascade="all, delete-orphan")
    # workers assigned to projec
    worker_team = relationship(
        "User",
        secondary=ProjectWorkerTeam.__tablename__,
        back_populates="assigned_projects"
    )
#db for chat, session
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String)
    content = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    session = relationship("SessionRecord")

#do not confuse with authorization, its just for the chat
class SessionRecord(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="sessions")
