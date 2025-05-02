from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from tickets.schemas import user as user_schema
from tickets.database import get_db
from tickets.repository import user as user_repository
from tickets.oauth2 import get_current_user
from tickets import models
from typing import List

router = APIRouter(prefix="/teams/{team_id}", tags=["Team Members"])
#decided to make it into def cause too many times used this
def _ensure_member(user:models.User, team_id: int):
    if not any(t.id == team_id for t in user.teams):
        raise HTTPException(status_code=403, detail="Team not available.")

#below is all the endpoints
@router.get("/users", response_model=List[user_schema.ShowUser])
def list_team_users(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_member(current_user, team_id)
    return user_repository.get_users_in_team(db, team_id)

@router.get("/available-admins", response_model=List[user_schema.ShowUser])
def available_admins(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_member(current_user, team_id)
    return user_repository.get_available_admins_in_team(db, team_id)

@router.get("/available-users", response_model=List[user_schema.ShowUser])
def available_users(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_member(current_user, team_id)
    # роль "user" → все пользователи (кроме админов) в команде
    return [u for u in user_repository.get_users_in_team(db, team_id) if u.role == models.UserRole.user]

@router.get("/users/{user_id}", response_model=user_schema.ShowUser)
def get_user(
    user_id: int,
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_member(current_user, team_id)
    user = user_repository.get_user_by_id(db, user_id)
    if team_id not in [t.id for t in user.teams]:
        raise HTTPException(status_code=404, detail="User not in this team")
    return user

@router.put("/availability", response_model=user_schema.ShowUser)
def update_my_availability(
    is_available: bool,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Юзер меняет своё поле is_available (команда не важна)."""
    current_user.is_available = is_available
    db.commit()
    db.refresh(current_user)
    return current_user