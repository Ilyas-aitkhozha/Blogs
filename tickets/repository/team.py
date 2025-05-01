from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from tickets import models
from tickets.schemas.team import TeamCreate

def _raise_not_found() -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Команда не найдена."
    )

def create_team(
    db: Session,
    creator: models.User,
    payload: TeamCreate,
) -> models.Team:
    team = models.Team(name=payload.name)
    try:
        db.add(team)
        db.flush()  # генерируем id / code до коммита
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Не удалось создать команду (ошибка уникальности)."
        )

    creator.team_id = team.id
    db.commit()
    db.refresh(team)
    return team


def join_team(
    db: Session,
    user: models.User,
    code: str,
) -> models.Team:
    team = db.query(models.Team).filter(
        models.Team.code == code.upper()
    ).first()
    if not team:
        _raise_not_found()

    user.team_id = team.id
    db.commit()
    return team


def leave_team(
    db: Session,
    user: models.User,
) -> None:
    if user.team_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы не состоите в команде."
        )
    user.team_id = None
    db.commit()


def get_team_by_id(
    db: Session,
    team_id: int,
) -> models.Team:
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        _raise_not_found()
    return team


def get_user_team(
    db: Session,
    user: models.User,
) -> Optional[models.Team]:
    if not user.team_id:
        return None
    return get_team_by_id(db, user.team_id)


def list_team_members(
    db: Session,
    team: models.Team,
) -> List[models.User]:
    return (
        db.query(models.User)
        .filter(models.User.team_id == team.id)
        .all()
    )
