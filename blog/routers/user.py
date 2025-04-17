from fastapi import APIRouter,Depends, status
from typing import List
from .. import database, schemas
from sqlalchemy.orm import Session
from ..repository import user


router = APIRouter(
    prefix = '/user',
    tags = ["Users"]
)

get_db = database.get_db

@router.get("/", response_model=List[schemas.ShowUser])
def get_all_users(db:Session = Depends(get_db)):
    return user.show_all(db)

@router.get("/{id}", response_model = schemas.ShowUser)
def get_user_by_id(id:int, db:Session = Depends(get_db)):
    return user.show(id, db)


@router.post("/", response_model = schemas.ShowUser,status_code = status.HTTP_201_CREATED)
def create_user(request: schemas.User,  db:Session = Depends(get_db)):
    return user.create(request, db)


@router.delete("/{id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_user_by_id(id: int, db:Session = Depends(get_db)):
    return user.delete_by_id(id, db)