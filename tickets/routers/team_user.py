from fastapi import APIRouter, Depends, HTTPException, Path, status, Response, Query
from sqlalchemy.orm import Session
from typing import List
from tickets.schemas import user as user_schema
from tickets.database import get_db
from tickets.repository import user as user_repository
from tickets.oauth2 import get_current_user
from tickets import models
from tickets.routers.dependencies import require_team_member
from ..enums import TeamRole

router = APIRouter(prefix="/teams/{team_id}", tags=["Team Members"])

def _ensure_member(user: models.User, team_id: int):
    if not any(t.id == team_id for t in user.teams):
        raise HTTPException(status_code=403, detail="Team not available.")

def _ensure_team_admin(user: models.User, team_id: int):
    if not any(ut.team_id == team_id and ut.role is TeamRole.admin for ut in user.user_teams):
        raise HTTPException(status_code=403, detail="Requires team admin role.")

#----------------------- GET logics
@router.get(
    "/users",
    response_model=List[user_schema.UserBrief],
)
def list_team_user_names(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_team_member),
):
    _ensure_member(current_user, team_id)
    return user_repository.get_team_user_briefs(db, team_id)

@router.get(
    "/available-admins",
    response_model=List[user_schema.UserBrief],
)
def available_admins(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_team_member),
):
    _ensure_member(current_user, team_id)
    return user_repository.get_available_admin_briefs(db, team_id)

@router.get(
    "/available-users",
    response_model=List[user_schema.UserBrief],
)
def available_members(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_team_member),
):
    _ensure_member(current_user, team_id)
    users = user_repository.get_available_users_by_role(
        db,
        role=TeamRole.member.value,
        team_id=team_id
    )
    return [user_schema.UserBrief.model_validate(u) for u in users]

@router.get(
    "/users/{user_id}",
    response_model=user_schema.ShowUser,
)
def get_user(
    user_id: int,
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_team_member),
):
    _ensure_member(current_user, team_id)
    user = user_repository.get_user_by_id(db, user_id)
    if team_id not in [t.id for t in user.teams]:
        raise HTTPException(status_code=404, detail="User not in this team")
    return user

#---- Update Logics
@router.put("/availability", response_model=user_schema.ShowUser)
def update_my_availability(
    is_available: bool,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    current_user.is_available = is_available
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post(
    "/members/{user_id}",
    response_model=user_schema.ShowUser,
    status_code=status.HTTP_201_CREATED
)
def add_user_to_team(
    user_id: int = Path(..., ge=1),
    team_id: int = Path(..., ge=1),
    role: TeamRole = Query(TeamRole.member),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_team_admin(current_user, team_id)
    if any(ut.team_id == team_id for ut in db.query(models.UserTeam).filter_by(user_id=user_id)):
        raise HTTPException(status_code=400, detail="User already in team")
    association = models.UserTeam(user_id=user_id, team_id=team_id, role=role)
    db.add(association)
    db.commit()
    return user_repository.get_user_by_id(db, user_id)

@router.delete(
    "/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_user_from_team(
    user_id: int = Path(..., ge=1),
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_team_admin(current_user, team_id)
    deleted = (
        db.query(models.UserTeam)
          .filter_by(user_id=user_id, team_id=team_id)
          .delete()
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="User not in this team")
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)