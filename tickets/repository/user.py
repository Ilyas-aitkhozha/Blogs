from sqlalchemy.orm import Session
from fastapi import HTTPException
from pydantic import EmailStr
from tickets import models
from tickets.hashing import Hash
from tickets.schemas.user import UserCreate
from sqlalchemy import func
from tickets.models import UserRole, TicketStatus

def create_user(db: Session, user: UserCreate):
    new_user = models.User(
        name=user.name,
        email=str(user.email),
        password=Hash.bcrypt(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user_by_id(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    return user

def get_user_by_email(db: Session, email: EmailStr):
    return db.query(models.User).filter(models.User.email == email).first()

def get_all_users(db: Session):
    return db.query(models.User).all()

def get_available_users_by_role(db: Session, role: str):
    return db.query(models.User).filter(
        models.User.role == role,
        models.User.is_available == True
    ).all()

def count_open_tickets_by_user(db, user_id: int):
        user = db.query(models.Ticket).filter(models.Ticket.assigned_to == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")

def get_least_loaded_admin(db: Session):
    counts_subq = (
        db.query(
            models.Ticket.assigned_to.label("admin_id"),
            func.count(models.Ticket.id).label("open_count")
        )
        .join(models.User, models.User.id == models.Ticket.assigned_to)
        .filter(
            models.User.role == UserRole.admin,
            models.User.is_available == True,
            models.Ticket.status == TicketStatus.open
        )
        .group_by(models.Ticket.assigned_to)
        .subquery()
    )
    result = (
        db.query(
            models.User,
            func.coalesce(counts_subq.c.open_count, 0).label("open_count")
        )
        .outerjoin(counts_subq, models.User.id == counts_subq.c.admin_id)
        .filter(
            models.User.role == UserRole.admin,
            models.User.is_available == True
        )
        .order_by("open_count")
        .first()
    )
    if result:
        user, open_count = result
        return user
    return None