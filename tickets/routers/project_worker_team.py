from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List

from tickets.database import get_db
import tickets.repository.project_worker_team as repo
from tickets.schemas.project_worker_team import ProjectWorkerTeamBase, ProjectWorkerTeamRead
from tickets.schemas.team import TeamBriefInfo
from tickets.schemas.project import ProjectBrief
from tickets.schemas.user import UserBrief

router = APIRouter(prefix="/projects/{project_id}/worker-team", tags=["Worker Teams"])

@router.post("/",response_model=ProjectWorkerTeamRead,status_code=status.HTTP_201_CREATED)
def assign_team(
    project_id: int,
    payload: ProjectWorkerTeamBase,
    db: Session = Depends(get_db)
) -> ProjectWorkerTeamRead:
    try:
        link = repo.assign_worker_team(db, project_id, payload.team_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return link
