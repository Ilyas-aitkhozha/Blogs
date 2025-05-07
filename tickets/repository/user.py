from typing import List, Optional
from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from tickets import models
from tickets.hashing import Hash
from tickets.schemas.user import UserCreate, UserBrief
from tickets.models import User, UserTeam, ProjectUser
from tickets.enums import *

#--------------------------- GET LOGICS
def get_user_by_id(db: Session, user_id: int) -> models.User:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user

def get_user_by_email(db: Session, email: EmailStr) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_team_members(
    db: Session,
    team_id: int,
    role: TeamRole = TeamRole.member
) -> List[User]:
    return (
        db.query(User)
          .join(UserTeam, UserTeam.user_id == User.id)
          .filter(
              UserTeam.team_id == team_id,
              UserTeam.role    == role.value
          )
          .all()
    )

def get_available_admins_in_team(db: Session, team_id: int) -> List[models.User]:
    return (
        db.query(models.User)
          .join(UserTeam, UserTeam.user_id == User.id)
          .filter(
              UserTeam.team_id == team_id,
              UserTeam.role    == TeamRole.admin.value,
              models.User.is_available.is_(True)
          )
          .all()
    )

def get_available_admin_briefs(db: Session, team_id: int) -> List[UserBrief]:
    admins = get_available_admins_in_team(db, team_id)
    unique = {u.id: u for u in admins}.values()
    return [UserBrief.model_validate(u) for u in unique]

def get_least_loaded_admins(db: Session, team_id: int, limit: int = 5) -> List[models.User]:
    subq = (
        db.query(
            models.Ticket.assigned_to.label("admin_id"),
            func.count(models.Ticket.id).label("open_count"),
        )
        .filter(
            models.Ticket.team_id == team_id,
            models.Ticket.status == models.TicketStatus.open,
        )
        .group_by(models.Ticket.assigned_to)
        .subquery()
    )

    results = (
        db.query(
            models.User,
            func.coalesce(subq.c.open_count, 0).label("open_count"),
        )
        .outerjoin(subq, models.User.id == subq.c.admin_id)
        .join(UserTeam, UserTeam.user_id == models.User.id)
        .filter(
            UserTeam.team_id == team_id,
            UserTeam.role    == TeamRole.admin.value,
            models.User.is_available.is_(True),
        )
        .order_by("open_count")
        .limit(limit)
        .all()
    )
    return [user for user, _ in results]

# in team
def get_available_users_by_role(
    db: Session,
    role: str,
    team_id: int,
    limit: Optional[int] = None
) -> List[models.User]:
    if role == TeamRole.admin.value or role == "admin":
        users = get_available_admins_in_team(db, team_id)
    else:
        users = get_team_members(db, team_id, TeamRole.member)
    return users[:limit] if limit else users
# in project
def get_project_users_by_role(
    db: Session,
    project_id: int,
    role: ProjectRole,
    limit: Optional[int] = None
) -> List[models.User]:
    q = (
        db.query(User)
          .join(ProjectUser, ProjectUser.user_id == User.id)
          .filter(
              ProjectUser.project_id == project_id,
              ProjectUser.role       == role
          )
    )
    if limit:
        q = q.limit(limit)
    return q.all()

def get_available_users_by_project(
    db: Session,
    project_id: int
) -> List[User]:
    stmt = (
        select(User)
        .join(ProjectUser, ProjectUser.user_id == User.id)
        .where(ProjectUser.project_id == project_id)
    )
    return db.execute(stmt).scalars().all()

def get_team_user_briefs(db: Session, team_id: int) -> List[UserBrief]:
    members = get_team_members(db, team_id, role=TeamRole.member)
    admins  = get_available_admins_in_team(db, team_id)
    unique  = {u.id: u for u in members + admins}.values()
    return [UserBrief.model_validate(u) for u in unique]

#---------------CREATE LOGICS
def create_user(db: Session, payload: UserCreate) -> models.User:
    hashed_pwd = Hash.bcrypt(payload.password)
    user = models.User(name=payload.name, password=hashed_pwd)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
