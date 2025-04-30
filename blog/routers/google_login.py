from fastapi import Request, HTTPException
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from dotenv import load_dotenv
import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from blog import models, jwttoken
from blog.database import get_db
load_dotenv()

config = Config(".env")
oauth = OAuth(config)
router = APIRouter(tags=["Google_login"])
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://www.googleapis.com/oauth2/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'}
)

@router.get("/auth/google")
async def login_via_google(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth/google/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = await oauth.google.parse_id_token(request, token)
    email = user_info.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="Google login failed")

    # check if user exists
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(email=email, role="user", password="oauth")  # Fake password
        db.add(user)
        db.commit()
        db.refresh(user)

    jwt_token = jwttoken.create_access_token(data={"sub": str(user.id)})
    return RedirectResponse(url=f"/docs?token={jwt_token}")