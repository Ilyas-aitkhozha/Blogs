# routers/team.py
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from tickets.database import get_db
from tickets import models
from tickets.schemas.team import TeamCreate, TeamOut, JoinTeam, TeamBriefInfo
from tickets.repository import team as team_repo
from tickets.oauth2 import get_current_user

router = APIRouter(prefix="/teams", tags=["Teams"])
#getting the list of all teams
@router.get("/check", response_model=List[TeamBriefInfo])
def get_teams(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return team_repo.get_user_teams(db, current_user)
@router.post("/", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(payload: TeamCreate,
                db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    return team_repo.create_team(db, current_user, payload)


@router.post("/join", response_model=TeamOut)
def join_team(payload: JoinTeam,
              db: Session = Depends(get_db),
              current_user: models.User = Depends(get_current_user)):
    return team_repo.join_team(db, current_user, payload.code)
