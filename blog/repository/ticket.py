from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from .. import schemas, models
from ..oaut2 import get_current_user


def get_all(db:Session):
    return db.query(models.Blog).all()

def get_all_yours(db: Session, current_user: models.User):
    return db.query(models.Blog).filter(models.Blog.user_id == current_user.id).all()


def create(db: Session, request: schemas.Blog, current_user: models.User):
    new_blog = models.Blog(title=request.title, body=request.body, user_id=current_user.id)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog


def delete(id: int, db: Session, current_user: models.User):
    q = db.query(models.Blog).filter(
        models.Blog.id == id,
        models.Blog.user_id == current_user.id  # чтобы удалять только свой
    )
    obj = q.first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"Blog {id} not found")
    q.delete(synchronize_session=False)
    db.commit()
    return {"detail": f"Deleted blog {id}"}


def update(id: int, request: schemas.Blog, db: Session, current_user: models.User):
    q = db.query(models.Blog).filter(
        models.Blog.id == id,
        models.Blog.user_id == current_user.id
    )
    if not q.first():
        raise HTTPException(status_code=404, detail=f"Blog {id} not found")
    q.update(request.model_dump())
    db.commit()
    return {"detail": "Updated"}


def show(id: int, db: Session, current_user: models.User):
    obj = db.query(models.Blog).filter(
        models.Blog.id == id,
        models.Blog.user_id == current_user.id
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"Blog {id} not found")
    return obj
