from fastapi import APIRouter, Depends, HTTPException, status, Response, Path
from sqlalchemy.orm import Session
from typing import List

from tickets.database import get_db
from tickets.routers.dependencies import require_project_admin, require_project_member
from tickets.schemas.project_worker_team import ProjectWorkerTeamBase, ProjectWorkerTeamRead
from tickets.schemas.team import TeamBriefInfo
from tickets.schemas.project import ProjectBrief
from tickets.schemas.user import UserBrief

import tickets.repository.project_worker_team as repo

router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}/worker-team",
    tags=["Worker Teams"],
)

@router.post(
    "/",
    response_model=ProjectWorkerTeamRead,
    status_code=status.HTTP_201_CREATED,
)
def assign_team(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    payload: ProjectWorkerTeamBase = ...,
    db: Session = Depends(get_db),
    _current_user=Depends(require_project_admin),
) -> ProjectWorkerTeamRead:
    try:
        # теперь используем team_id из пути
        raw = repo.assign_worker_team_to_project(db, project_id, team_id)
        return ProjectWorkerTeamRead.model_validate(raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/",
    response_model=ProjectWorkerTeamRead,
)
def read_team(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    _current_user=Depends(require_project_member),
) -> ProjectWorkerTeamRead:
    raw = repo.get_worker_team_of_project(db, project_id)
    if not raw:
        raise HTTPException(status_code=404, detail="No worker-team assigned to this project")
    return ProjectWorkerTeamRead.model_validate(raw)

@router.patch(
    "/",
    response_model=ProjectWorkerTeamRead,
)
def reassign_team(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    payload: ProjectWorkerTeamBase = ...,
    db: Session = Depends(get_db),
    _current_user=Depends(require_project_admin),
) -> ProjectWorkerTeamRead:
    try:
        # используем team_id из пути
        raw = repo.update_worker_team_for_project(db, project_id, team_id)
        return ProjectWorkerTeamRead.model_validate(raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unassign_team(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    _current_user=Depends(require_project_admin),
) -> Response:
    repo.remove_worker_team_from_project(db, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get(
    "/available-workers",
    response_model=List[UserBrief],
)
def available_workers(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    _current_user=Depends(require_project_member),
) -> List[UserBrief]:
    raws = repo.get_available_workers_by_project(db, project_id)
    return [UserBrief.model_validate(u) for u in raws]

@router.get(
    "/available",
    response_model=List[TeamBriefInfo],
)
def list_free_teams(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    _current_user=Depends(require_project_member),
) -> List[TeamBriefInfo]:
    raws = repo.list_worker_teams(db)
    return [TeamBriefInfo.model_validate(t) for t in raws]

@router.get(
    "/unassigned-projects",
    response_model=List[ProjectBrief],
)
def list_projects_needing_team(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    _current_user=Depends(require_project_admin),
) -> List[ProjectBrief]:
    raws = repo.list_projects_without_worker_team(db)
    return [ProjectBrief.model_validate(p) for p in raws]
