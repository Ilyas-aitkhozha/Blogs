from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from . import jwttoken
from . import models, database
from sqlalchemy.orm import Session



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login_in_site", auto_error=False)
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)) -> models.User:
    print("get_current_user is called")
    if not token:
        print("No token in header, trying cookies")
        token = request.cookies.get("access_token")
    if not token:
        print("No token in header or cookies")
        raise credentials_exception
    try:
        user_id = jwttoken.verify_token(token, credentials_exception)
        print("Token verified, checking user_id in db")
    except Exception as e:
        print(f"❌ Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise credentials_exception
    print("Authentication successful")
    return user
