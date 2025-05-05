from typing import List
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from tickets import models
from tickets.enums import *
from tickets.models import UserTeam
from tickets.schemas.team import TeamCreate
from tickets.schemas.team import TeamBriefInfo

#helper
def _raise_not_found() -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="team not found."
    )

#---------------------------------CREATE LOGICS
def create_team(db: Session,creator: models.User,payload: TeamCreate) -> models.Team:
    team = models.Team(name=payload.name)
    try:
        db.add(team)
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not create team: name already exists."
        )

    association = UserTeam(
        user_id=creator.id,
        team_id=team.id,
        role=TeamRole.admin
    )
    db.add(association)
    db.commit()
    db.refresh(team)
    return team

#----------------- GET LOGICS
def get_team_by_id(
    db: Session,
    team_id: int,
) -> models.Team:
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        _raise_not_found()
    return team



def get_user_teams(
    db: Session,
    user: models.User,
) -> List[TeamBriefInfo]:
    teams = db.query(models.Team).join(models.Team.members).filter(models.User.id == user.id).all()
    return [TeamBriefInfo.model_validate(team) for team in teams]





def join_team(db: Session,user: models.User,code: str) -> models.Team:
    team = (
        db.query(models.Team).filter(models.Team.code == code.upper()).first())
    if not team:
        _raise_not_found()
    exists = (db.query(UserTeam).filter_by(user_id=user.id, team_id=team.id).first())
    if not exists:
        association = UserTeam(user_id=user.id,team_id=team.id,role=TeamRole.member)
        db.add(association)
        db.commit()
    db.refresh(team)
    return team


def leave_team(db: Session,user: models.User,team_id: int) -> None:
    team = next((t for t in user.teams if t.id == team_id), None)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not in this team."
        )

    user.teams.remove(team)
    db.commit()


def list_team_members(
    db: Session,
    team_id: int,
) -> List[models.User]:
    return (
        db.query(models.User)
        .filter(models.User.teams.any(models.Team.id == team_id))
        .all()
    )
