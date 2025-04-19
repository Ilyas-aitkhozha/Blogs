from fastapi import APIRouter, Depends, status
from .. import schemas, database, oaut2
from typing import List
from sqlalchemy.orm import Session
from ..repository import blog

router = APIRouter(
    prefix="/blog",
    tags = ['blogs']

)


get_db = database.get_db


@router.get("/", response_model=List[schemas.Showblog])
def get_all_blogs(db: Session = Depends(get_db)):
    return blog.get_all(db)

@router.get("/yours", response_model=List[schemas.Showblog])
def get_your_blogs(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(oaut2.get_current_user)
):
    return blog.get_all_yours(db, current_user)


@router.post("/", status_code = status.HTTP_201_CREATED)
def create(request:schemas.Blog, db:Session = Depends(get_db),current_user: schemas.User = Depends(oaut2.get_current_user)):
    return blog.create(db, request, current_user)

@router.delete("/{id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_blog_by_id(id: int, db:Session = Depends(get_db), current_user: schemas.User = Depends(oaut2.get_current_user)):
    return blog.delete(id, db, current_user)

@router.put('/{id}', status_code = status.HTTP_202_ACCEPTED)
def update_blog_by_id(id:int, request:schemas.Blog, db:Session = Depends(get_db), current_user: schemas.User = Depends(oaut2.get_current_user)):
    return blog.update(id, request, db, current_user)

@router.get("/{id}", status_code=status.HTTP_200_OK, response_model = schemas.Showblog)
def get_blog_by_id(id:int, db:Session = Depends(get_db), current_user: schemas.User = Depends(oaut2.get_current_user)):
    return blog.show(id, db, current_user)
