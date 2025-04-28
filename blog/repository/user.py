from sqlalchemy.orm import Session
from blog import models
from blog.hashing import Hash
from blog.schemas.user import UserCreate
from pydantic import EmailStr
from fastapi import HTTPException

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
