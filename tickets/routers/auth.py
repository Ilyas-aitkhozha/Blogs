from fastapi import APIRouter, Depends, Request, HTTPException, status
from starlette.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from sqlalchemy.orm import Session
import os
from tickets import models, jwttoken
from tickets.database import get_db
from tickets.hashing import Hash
from tickets.schemas.auth import Token
from tickets.schemas.user import ShowUser
from tickets.oauth2 import get_current_user
from tickets.jwttoken import ACCESS_TOKEN_EXPIRE_MINUTES
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

@router.get("/", tags = ["Auth"])
def get_auth_options():
    #(for frontend)
    return {
        "available_methods": {
            "login_via_site": "/auth/login_in_site",
            "login_via_google": "/auth/google"
        }
    }


# — обычный логин
@router.post("/login_in_site", response_model=ShowUser, tags=["Auth"])
def login_or_register_via_site(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    username = form_data.username
    password = form_data.password
    user = db.query(models.User).filter(models.User.name == username).first()
    if not user:
        new_user = models.User(
            name=username,
            email=f"{username}@local",  # dummy email to satisfy DB
            password=Hash.bcrypt(password),
            role="user",
            is_available=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user
    else:
        if not Hash.verify(user.password, password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учётные данные",
                headers={"WWW-Authenticate": "Bearer"},
            )
    token = jwttoken.create_access_token({"sub": str(user.id)})

    response = JSONResponse(content=ShowUser.from_attributes(user).dict())
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,  # True, если HTTPS
        samesite="none",  # или "lax", в зависимости от ваших нужд
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return response

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
async def google_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    # 1) Exchange the code for tokens
    try:
        oauth_token = await oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state or token"
        )

    # 2) Fetch user info
    resp = await oauth.google.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        token=oauth_token
    )
    info = resp.json()
    email = info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google login failed: no email returned"
        )

    # 3) Lookup or create the user
    user = db.query(models.User).filter_by(email=email).first()
    if not user:
        user = models.User(
            name=info.get("name", ""),
            email=email,
            role="user",
            password="oauth"  # placeholder
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 4) Issue our JWT
    jwt_token = jwttoken.create_access_token({"sub": str(user.id)})

    response = RedirectResponse(url=FRONTEND)  # просто на корень SPA
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return response