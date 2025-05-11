from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, Text, DateTime, Enum as SqlEnum
from sqlalchemy.orm import relationship
import random, string
from datetime import datetime, timezone
from .database import Base
from .enums import TeamRole, ProjectRole, TicketStatus, TicketPriority, TicketType

# helper to generate team codes

def _generate_team_code(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


class UserTeam(Base):
    __tablename__ = "user_teams"
    user_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    team_id   = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
    role      = Column(SqlEnum(TeamRole, native_enum=False), nullable=False, default=TeamRole.member)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user      = relationship("User", back_populates="user_teams")
    team      = relationship("Team", back_populates="user_teams")


class ProjectUser(Base):
    __tablename__ = "project_users"
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    role       = Column(SqlEnum(ProjectRole, native_enum=False), nullable=False, default=ProjectRole.member)
    joined_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user       = relationship("User", back_populates="project_users")
    project    = relationship("Project", back_populates="project_users")


class Team(Base):
    __tablename__ = "teams"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, nullable=False)
    code        = Column(String, unique=True, index=True, default=_generate_team_code)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user_teams  = relationship("UserTeam", back_populates="team", cascade="all, delete-orphan")
    projects    = relationship("Project", back_populates="team")
    members     = relationship("User", secondary="user_teams", back_populates="teams", overlaps="user_teams")


class User(Base):
    __tablename__ = 'users'
    id                   = Column(Integer, primary_key=True, index=True)
    name                 = Column(String, nullable=False)
    email                = Column(String, nullable=True)
    password             = Column(String, nullable=False)
    is_available         = Column(Boolean, default=True)

    user_teams           = relationship("UserTeam", back_populates="user", cascade="all, delete-orphan", overlaps="teams")
    teams                = relationship("Team", secondary="user_teams", back_populates="members", overlaps="user_teams")
    project_users        = relationship("ProjectUser", back_populates="user", cascade="all, delete-orphan")

    tickets_created      = relationship(
        "Ticket",
        back_populates="creator",
        foreign_keys="Ticket.created_by",
        cascade="all, delete-orphan"
    )
    tickets_assigned     = relationship(
        "Ticket",
        back_populates="assignee",
        foreign_keys="Ticket.assigned_to"
    )
    sessions             = relationship("SessionRecord", back_populates="user", cascade="all, delete-orphan")

    # новый код: администрируемые рабочие команды
    administered_worker_teams = relationship(
        "WorkerTeam",
        back_populates="admin",
        cascade="all, delete-orphan"
    )


class Ticket(Base):
    __tablename__ = "tickets"
    id             = Column(Integer, primary_key=True, index=True)
    title          = Column(String, nullable=False)
    description    = Column(String, nullable=False)
    status         = Column(SqlEnum(TicketStatus, native_enum=False), default=TicketStatus.open)
    priority       = Column(SqlEnum(TicketPriority, native_enum=False), default=TicketPriority.medium)
    confirmed      = Column(Boolean, default=False)
    feedback       = Column(String, nullable=True)

    created_by     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    assigned_to    = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    team_id        = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"))
    project_id     = Column(Integer, ForeignKey("projects.id"), nullable=True)

    created_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    accepted_at    = Column(DateTime, nullable=True)
    closed_at      = Column(DateTime, nullable=True)
    updated_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    type           = Column(SqlEnum(TicketType, native_enum=False), nullable=False, default=TicketType.worker)
    worker_team_id = Column(
        Integer,
        ForeignKey("worker_teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    worker_team = relationship(
        "WorkerTeam",
        back_populates="tickets",
        # ← use the actual Column object, not a string!
        foreign_keys=[worker_team_id],
    )

    creator        = relationship("User", back_populates="tickets_created", foreign_keys=[created_by])
    assignee       = relationship("User", back_populates="tickets_assigned", foreign_keys=[assigned_to])
    project        = relationship("Project", back_populates="tickets")


class Project(Base):
    __tablename__ = "projects"
    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String, nullable=False)
    description    = Column(Text)
    team_id        = Column(Integer, ForeignKey("teams.id"), nullable=False)
    created_by     = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    team           = relationship("Team", back_populates="projects")
    creator        = relationship("User")
    project_users  = relationship("ProjectUser", back_populates="project", cascade="all, delete-orphan")
    tickets        = relationship("Ticket", back_populates="project", cascade="all, delete-orphan")

    worker_team_id = Column(Integer, ForeignKey("worker_teams.id", ondelete="SET NULL"), nullable=True)
    worker_team    = relationship("WorkerTeam", back_populates="projects", uselist=False)


class WorkerTeam(Base):
    __tablename__ = "worker_teams"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # новый код: админ команды
    admin_id   = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin      = relationship("User", back_populates="administered_worker_teams")

    # связь с тикетами
    tickets    = relationship(
        "Ticket",
        back_populates="worker_team",
        foreign_keys=["Ticket.worker_team_id"]
    )
    # связь с проектами
    projects   = relationship(
        "Project",
        back_populates="worker_team",
        cascade="all, delete-orphan"
    )

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id         = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    role       = Column(String)
    content    = Column(String)
    timestamp  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    session    = relationship("SessionRecord")

class SessionRecord(Base):
    __tablename__ = "sessions"
    id         = Column(String, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user       = relationship("User", back_populates="sessions")
