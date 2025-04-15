from fastapi import FastAPI, Depends, status, Response, HTTPException
from typing import List
from . import schemas, models
from .database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.get("/blog", response_model=List[schemas.Showblog])
def get_blogs(db:Session = Depends(get_db)):
    blogs = db.query(models.Blog).all()
    return blogs

@app.get("/blog/{id}", status_code=status.HTTP_200_OK, response_model = schemas.Showblog)
def get_blog_by_id(id:int,response: Response, db:Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id == id).first()
    if not blog:
        raise HTTPException(status_code=404, detail=f"Blog with id {id} not found")
    return blog


@app.post("/blog", status_code = status.HTTP_201_CREATED)
def create(request:schemas.Blog, db:Session = Depends(get_db)):
    new_blog = models.Blog(title = request.title, body = request.body)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog


@app.delete("/blog/{id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_blog_by_id(id: int, db:Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id == id)
    if not blog.first():
        raise HTTPException(status_code=404, detail=f"Blog with id {id} not found")
    else:
        blog.delete(synchronize_session=False)
        db.commit()
        return f"blog with this id {id} was deleted"


@app.put('/blog/{id}', status_code = status.HTTP_202_ACCEPTED)
def update_blog_by_id(id, request:schemas.Blog, db:Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id == id)
    if not blog.first():
        raise HTTPException(status_code=404, detail=f"Blog with id {id} not found")
    blog.update(request.dict())
    db.commit()
    return "updated title"


@app.post("/user",status_code = status.HTTP_201_CREATED)
def create_user(request: schemas.User,  db:Session = Depends(get_db)):
    new_user = models.User(name=request.name, email=request.email, password=request.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/user", response_model=List[schemas.ShowUser])
def get_all_users(db:Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users

@app.delete("/user/{id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_user_by_id(id: int, db:Session = Depends(get_db)):
    users = db.query(models.User).filter(models.User.id==id)
    if not users:
        raise HTTPException(status_code=404, detail=f"user with id {id} not found")
    else:
        users.delete(synchronize_session=False)
        db.commit()
        return f"user with this id {id} was deleted"
