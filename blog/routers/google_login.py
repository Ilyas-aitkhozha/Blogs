from fastapi import Request, HTTPException, APIRouter, Depends
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from blog import models, jwttoken
from blog.database import get_db
import os

load_dotenv()

config = Config(".env")
oauth = OAuth(config)

router = APIRouter(tags=["Google_login"])

oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@router.get("/auth/google")
async def login_via_google(request: Request):
    redirect_uri = "https://ticketsystem-qfj9.onrender.com/auth/google/callback"  # hardcoded for stability
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth/google/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        resp = await oauth.google.get('userinfo', token=token)
        user_info = resp.json()

        email = user_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Google login failed: no email returned")

        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            user = models.User(email=email, role="user", password="oauth")  # dummy password
            db.add(user)
            db.commit()
            db.refresh(user)

        jwt_token = jwttoken.create_access_token(data={"sub": str(user.id)})
        return RedirectResponse(url=f"/docs?token={jwt_token}")

    except Exception as e:
        print("❌ Google OAuth callback error:", e)
        raise HTTPException(status_code=500, detail="OAuth callback failed")
