# blog/routers/user.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from blog.schemas import user as user_schema
from blog.database import get_db
from blog.repository import user as user_repository

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=user_schema.ShowUser)
def create_user(request: user_schema.UserCreate, db: Session = Depends(get_db)):
    return user_repository.create_user(db, request)

@router.get("/{id}", response_model=user_schema.ShowUser)
def get_user(id: int, db: Session = Depends(get_db)):
    return user_repository.get_user_by_id(db, id)

@router.get("/", response_model=list[user_schema.ShowUser])
def get_all_users(db: Session = Depends(get_db)):
    return user_repository.get_all_users(db)

@router.get("/available-admins", response_model=list[user_schema.ShowUser])
def get_available_admins(db: Session = Depends(get_db)):
    from blog.repository import user as user_repository
    return user_repository.get_available_users_by_role(db, "admin")

@router.get("/available-users", response_model=list[user_schema.ShowUser])
def get_available_users(db: Session = Depends(get_db)):
    from blog.repository import user as user_repository
    return user_repository.get_available_users_by_role(db, "user")
