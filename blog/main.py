from fastapi import FastAPI
from . import models
from .database import engine
from .routers import blog, user, login, chat_bot


app = FastAPI(

)

models.Base.metadata.create_all(bind=engine)

app.include_router(login.router)
app.include_router(blog.router)
app.include_router(user.router)
app.include_router(chat_bot.router)




