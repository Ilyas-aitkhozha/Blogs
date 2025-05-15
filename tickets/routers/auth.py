from fastapi import APIRouter, Depends, Request, HTTPException, status, Response
from starlette.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
import os
import logging
from tickets.schemas.auth import Login
from tickets.models import User
from tickets import models, jwttoken
from tickets.database import get_db
from tickets.hashing import Hash
from tickets.schemas.user import ShowUser
from tickets.oauth2 import get_current_user
from tickets.jwttoken import ACCESS_TOKEN_EXPIRE_MINUTES
from tickets.schemas.team import TeamWithProjects
from tickets.schemas.project import ProjectMembership
logger = logging.getLogger(__name__)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"
FRONTEND = os.getenv("FRONTEND_URL") if IS_PRODUCTION else os.getenv("FRONTEND_LOCAL_URL")
router = APIRouter(prefix="/auth", tags=["Auth"])

# OAuth setup
config = Config(".env")
oauth = OAuth(config)
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/", tags=["Auth"])
def login_or_register_via_site(
    payload: Login,
    db: Session = Depends(get_db),
):
    token = jwttoken.create_access_token({"sub": str(user.id)})

    user_out = build_user_response(user)

    payload = jsonable_encoder(user_out)

    response = JSONResponse(content=payload, status_code=status.HTTP_200_OK)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="none" if IS_PRODUCTION else "lax",
        path="/",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response

def build_user_response(user: User) -> ShowUser:
    teams_data = []
    for ut in user.user_teams:
        #checks projects in particular team
        projects_data = []
        for pu in user.project_users:
            if pu.project.team_id == ut.team_id:
                projects_data.append(ProjectMembership(project=pu.project,role=pu.role,joined_at=pu.joined_at))
        teams_data.append(
            TeamWithProjects(team=ut.team,role=ut.role,joined_at=ut.joined_at,projects=projects_data))
    return ShowUser(
        id=user.id,
        name=user.name,
        email=user.email,
        is_available=user.is_available,
        teams=teams_data
    )
@router.get("/me", response_model=ShowUser)
def get_me(current_user: models.User = Depends(get_current_user)):
    return build_user_response(current_user)

@router.get("/google")
async def login_via_google(request: Request):
    logger.info("▶️ login_via_google вызван")
    redirect_uri = f"{os.getenv('BACKEND_URL')}/auth/google/callback"
    logger.info("redirect_uri =", redirect_uri)
    try:
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except Exception as e:
        logger.error("❌ authorize_redirect упал:", repr(e))
        raise


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    # 1) Exchange code for tokens
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
            password="oauth"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 4) Issue our JWT
    jwt_token = jwttoken.create_access_token({"sub": str(user.id)})

    # 5) Redirect back to SPA + set cookie for all paths
    response = RedirectResponse(url=FRONTEND)
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="none" if IS_PRODUCTION else "lax",
        path="/",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return response

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Auth"]
)
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=None,
        secure=IS_PRODUCTION,
        samesite="none" if IS_PRODUCTION else "lax",
    )
