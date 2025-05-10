import os
from fastapi import FastAPI
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .database import engine
from .routers import team_ticket, team_user, chat_bot, auth, team, analytics, project, project_worker_team

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# URL-ы
FRONTEND_URL = os.getenv("FRONTEND_URL")
FRONTEND_LOCAL_URL = os.getenv("FRONTEND_LOCAL_URL")

origins = []
if IS_PRODUCTION and FRONTEND_URL:
    origins.append(FRONTEND_URL)
elif FRONTEND_LOCAL_URL:
    origins.append(FRONTEND_LOCAL_URL)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "super-secret-session")
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(team_user.router)
app.include_router(team_ticket.router)
app.include_router(chat_bot.router)
app.include_router(team.router)
app.include_router(auth.router)
app.include_router(analytics.router)
app.include_router(project.router)
app.include_router(project_worker_team.router)
@app.get("/ping")
def ping():
    return {"message": "pong"}

