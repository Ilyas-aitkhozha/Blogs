from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from blog import models, jwttoken
from blog.schemas.auth import Token
from blog.hashing import Hash
from blog.schemas import user
from blog.oaut2 import get_current_user
from blog.database import get_db

router = APIRouter(tags=["Login"])

@router.get("/auth/me", response_model=user.ShowUser)
def get_me(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return current_user

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not Hash.verify(user.password, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = jwttoken.create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
