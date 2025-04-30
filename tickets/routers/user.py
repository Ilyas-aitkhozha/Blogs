from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from tickets.schemas import user as user_schema
from tickets.database import get_db
from tickets.repository import user as user_repository
from tickets.oaut2 import get_current_user
from tickets import models

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=user_schema.ShowUser)
def create_user(request: user_schema.UserCreate, db: Session = Depends(get_db)):
    return user_repository.create_user(db, request)

@router.get("/", response_model=list[user_schema.ShowUser])
def get_all_users(db: Session = Depends(get_db)):
    return user_repository.get_all_users(db)

@router.get("/available-admins", response_model=list[user_schema.ShowUser])
def get_available_admins(db: Session = Depends(get_db)):
    return user_repository.get_available_users_by_role(db, "admin")

@router.get("/available-users", response_model=list[user_schema.ShowUser])
def get_available_users(db: Session = Depends(get_db)):
    return user_repository.get_available_users_by_role(db, "user")

@router.get("/{id}", response_model=user_schema.ShowUser)
def get_user(id: int, db: Session = Depends(get_db)):
    return user_repository.get_user_by_id(db, id)

@router.put("/availability", response_model=user_schema.ShowUser)
def update_availability(
    is_available: bool,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_available = is_available
    db.commit()
    db.refresh(user)
    return user