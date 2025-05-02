from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from . import jwttoken
from . import models, database
from sqlalchemy.orm import Session



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login_in_site", auto_error=False)


def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)) -> models.User:
    if not token:
        token = request.cookies.get("access_token")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    user_id = jwttoken.verify_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise credentials_exception
    return user
