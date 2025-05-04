from typing import List
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from tickets import models
from tickets.schemas.team import TeamCreate

#helper
def _raise_not_found() -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="team not found."
    )


def create_team(
    db: Session,
    creator: models.User,
    payload: TeamCreate,
) -> models.Team:
    team = models.Team(name=payload.name)
    try:
        db.add(team)
        db.flush()
    except IntegrityError:#rollabackaem if name isnt unique
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="couldnt create a team (unique error)."
        )

    creator.teams.append(team)

    db.commit()
    db.refresh(team)
    return team


def join_team(
    db: Session,
    user: models.User,
    code: str,
) -> models.Team:
    team = (
        db.query(models.Team)
        .filter(models.Team.code == code.upper())
        .first()
    )
    if not team:
        _raise_not_found()

    if team not in user.teams:          # not to duplicate
        user.teams.append(team)

    db.commit()
    db.refresh(team)
    return team


def leave_team(
    db: Session,
    user: models.User,
    team_id: int,
) -> None:
    team = next((t for t in user.teams if t.id == team_id), None)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not in this team."
        )

    user.teams.remove(team)
    db.commit()


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
) -> List[models.Team]:
    # all teams that user in
    return user.teams


def list_team_members(
    db: Session,
    team_id: int,
) -> List[models.User]:
    return (
        db.query(models.User)
        .filter(models.User.teams.any(models.Team.id == team_id))
        .all()
    )
