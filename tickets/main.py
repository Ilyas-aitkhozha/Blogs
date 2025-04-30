import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .database import engine
from .routers import ticket, user, login, chat_bot, google_login

load_dotenv()

@asynccontextmanager
async def lifespan(_: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "super-secret-session")
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ticketsystem-c2sy.onrender.com","http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user.router)
app.include_router(ticket.router)
app.include_router(login.router)
app.include_router(chat_bot.router)
app.include_router(google_login.router)
