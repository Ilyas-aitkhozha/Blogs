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
    redirect_uri = "https://ticketsystem-qfj9.onrender.com/auth/google/callback"
    response = await oauth.google.authorize_redirect(request, redirect_uri)
    # DEBUG: print stored CSRF state
    session_key = f"{oauth.google.name}_oauth_state"
    print("🔐 [login] session state:", request.session.get(session_key))
    return response

@router.get("/auth/google/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    session_key = f"{oauth.google.name}_oauth_state"
    # DEBUG: print stored vs. returned state
    print("🔐 [callback] session state:", request.session.get(session_key))
    print("🔐 [callback]  query  state:", request.query_params.get("state"))

    # Exchange the authorization code for a token
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        print("❌ CSRF/state mismatch or token error:", e)
        raise HTTPException(status_code=400, detail="Invalid OAuth state or token")

    # Retrieve user info from Google
    resp = await oauth.google.get(
        'https://www.googleapis.com/oauth2/v1/userinfo',
        token=token
    )
    user_info = resp.json()
    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google login failed: no email returned")

    # Get or create the user in the database
    user = db.query(models.User).filter_by(email=email).first()
    if not user:
        full_name = user_info.get("name", "")
        user = models.User(
            name=full_name,
            email=email,
            role="user",
            password="oauth"  # placeholder
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Issue JWT and set as an HTTP-only cookie
    jwt_token = jwttoken.create_access_token(data={"sub": str(user.id)})
    response = RedirectResponse(url="/docs")
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        max_age=3600,
        samesite="lax"
    )
    return response
