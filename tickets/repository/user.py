from typing import List, Optional
from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session
from tickets import models
from tickets.hashing import Hash
from tickets.schemas.user import UserCreate


def get_user_by_id(db: Session, user_id: int) -> models.User:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user


def get_user_by_email(db: Session, email: EmailStr) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, payload: UserCreate) -> models.User:
    hashed_pwd = Hash.bcrypt(payload.password)
    user = models.User(name=payload.name, password=hashed_pwd)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_users_in_team(db: Session, team_id: int) -> List[models.User]:
    return (
        db.query(models.User)
        .filter(models.User.teams.any(models.Team.id == team_id))
        .all()
    )


def get_available_admins_in_team(db: Session, team_id: int) -> List[models.User]:
    return (
        db.query(models.User)
        .filter(
            models.User.role == models.UserRole.admin,
            models.User.is_available.is_(True),
            models.User.teams.any(models.Team.id == team_id),
        )
        .all()
    )


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
        .filter(
            models.User.role == models.UserRole.admin,
            models.User.is_available.is_(True),
            models.User.teams.any(models.Team.id == team_id),
        )
        .order_by("open_count")
        .limit(limit)
        .all()
    )
    return [user for user, _ in results]
def get_available_users_by_role(db: Session, role: str, team_id: int, limit: int | None = None):
    """
    Старая сигнатура: сохраняем, чтобы старые импорты не падали.
    • role == "admin"  → используем новую функцию get_available_admins_in_team
    • иначе            → просто список всех пользователей в команде
    """
    if role == models.UserRole.admin or role == "admin":
        admins = get_available_admins_in_team(db, team_id)
        return admins[:limit] if limit else admins
    else:
        users = get_users_in_team(db, team_id)
        return users[:limit] if limit else users