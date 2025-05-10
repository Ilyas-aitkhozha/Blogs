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

@router.get("/",response_model=ProjectWorkerTeamRead)
def read_team(
    project_id: int,
    db: Session = Depends(get_db)
) -> ProjectWorkerTeamRead:
    link = repo.get_worker_team(db, project_id)
    if not link:
        raise HTTPException(status_code=404, detail="No worker-team assigned to this project")
    return link

@router.patch("/",response_model=ProjectWorkerTeamRead)
def reassign_team(
    project_id: int,
    payload: ProjectWorkerTeamBase,
    db: Session = Depends(get_db)
) -> ProjectWorkerTeamRead:
    try:
        link = repo.update_worker_team(db, project_id, payload.team_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return link


@router.delete("/",status_code=status.HTTP_204_NO_CONTENT)
def unassign_team(
    project_id: int,
    db: Session = Depends(get_db)
) -> Response:
    repo.remove_worker_team(db, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/available-workers",response_model=List[UserBrief])
def available_workers(
    project_id: int,
    db: Session = Depends(get_db)
) -> List[UserBrief]:
    return repo.get_available_workers_by_project(db, project_id)

@router.get(
    "/available",
    response_model=List[TeamBriefInfo]
)
def list_free_teams(
    db: Session = Depends(get_db)
) -> List[TeamBriefInfo]:
    return repo.list_available_worker_teams(db)

@router.get(
    "/unassigned-projects",
    response_model=List[ProjectBrief]
)
def list_projects_needing_team(
    db: Session = Depends(get_db)
) -> List[ProjectBrief]:
    return repo.list_unassigned_projects(db)