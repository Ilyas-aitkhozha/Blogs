from fastapi import HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models
from ..hashing import Hash

def create(request:schemas.User, db:Session):
    new_user = models.User(name=request.name, email=request.email, password=Hash.bcrypt(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def show(id:int, db:Session):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"user with id {id} not found")
    return user

def delete_by_id(id:int, db:Session):
    users = db.query(models.User).filter(models.User.id == id)
    if not users:
        raise HTTPException(status_code=404, detail=f"user with id {id} not found")
    else:
        users.delete(synchronize_session=False)
        db.commit()
        return f"user with this id {id} was deleted"

def show_all(db):
    users = db.query(models.User).all()
    return users

