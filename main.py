import uvicorn
from fastapi import FastAPI
from typing import Optional
from pydantic import BaseModel
app = FastAPI()

@app.get("/blog")
def index(limit = 10, published: bool = True):
    if published:
        return {"data": f"{limit} published blogs from the db"}
    else:
        return {"data": f"{limit} blogs from the db"}

@app.get("/blog/unpublished")
def unpublished():
    return {"data": "all of the unpublished"}

@app.get("/blog/{blog_id}/{name}")
def blog_name(blog_id: int, name: str):
    return {"data": blog_id, "name": name}

@app.get("/blog/{blog_id}")
def show(blog_id: int):
    return {"data": blog_id}

@app.get("/blog/comments")
def comments(blog_id:int, limit = 10):
    return {"data": blog_id, "limit": limit}
class Blog(BaseModel):
    title: str
    body: str
    published_at: Optional[bool]

@app.post("/blog")
def create_blog(request:Blog):
    return {"data": f"blog is created with title {request.title}"}





#if __name__ == "__main__":
    #uvicorn.run(app, host = "127.0.0.1", port = 9000)