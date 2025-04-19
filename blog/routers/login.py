from fastapi import APIRouter, Depends, HTTPException
from .. import schemas, database, models,jwttoken
from sqlalchemy.orm import Session
from ..hashing import Hash
from fastapi.security import OAuth2PasswordRequestForm
router = APIRouter(
    tags = ["Login"]
)

@router.post("/login")
def login(request:OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == request.username).first()
    if not user or not Hash.verify(user.password, request.password):
        raise HTTPException(status_code=404, detail="Invalid credentials")
    access_token = jwttoken.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
