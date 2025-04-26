from fastapi import FastAPI
from . import models
from .database import engine
from .routers import blog, user, login, chat_bot
from contextlib import asynccontextmanager



@asynccontextmanager
async def lifespan(_: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(login.router)
app.include_router(blog.router)
app.include_router(user.router)
app.include_router(chat_bot.router)




