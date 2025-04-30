from fastapi import APIRouter, Depends, Request, HTTPException, status
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from sqlalchemy.orm import Session
import os
from tickets import models, jwttoken
from tickets.database import get_db
from tickets.hashing import Hash
from tickets.schemas.auth import Token
from tickets.schemas.user import ShowUser
from tickets.oaut2 import get_current_user
from fastapi.security import OAuth2PasswordRequestForm

# приводим всё к /auth
router = APIRouter(prefix="/auth", tags=["Auth"])

# настройка OAuth
config = Config(".env")
oauth = OAuth(config)
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

FRONTEND = os.getenv("FRONTEND_URL")  # куда редиректим после успеха

# — обычный логин
@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not Hash.verify(user.password, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учётные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = jwttoken.create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=ShowUser)
def get_me(
    current_user: models.User = Depends(get_current_user),
):
    return current_user

# — старт Google OAuth
@router.get("/google")
async def login_via_google(request: Request):
    redirect_uri = f"{os.getenv('BACKEND_URL')}/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

# — callback от Google
@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OAuth state/token")

    resp = await oauth.google.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        token=token
    )
    info = resp.json()
    email = info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google login failed")

    user = db.query(models.User).filter_by(email=email).first()
    if not user:
        user = models.User(
            name=info.get("name", ""),
            email=email,
            role="user",
            password="oauth"  # можно потом обновить
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    jwt_token = jwttoken.create_access_token(data={"sub": str(user.id)})

    response = RedirectResponse(url=os.getenv("FRONTEND_URL"))

    # ставим HttpOnly-куку
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=True,  # ставим True, если https
        samesite="none",  # для кросс-доменных куки
        max_age=3600,  # время жизни в секундах
        #domain=os.getenv("BACKEND_DOMAIN")  # опционально, если нужно указать домен
    )
    return response