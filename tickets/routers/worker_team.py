from fastapi import APIRouter, Depends, HTTPException, status, Response, Path
from sqlalchemy.orm import Session
from typing import List

from tickets.database import get_db
from tickets.routers.dependencies import require_project_admin
from tickets.schemas.worker_team import WorkerTeamCreate, WorkerTeamRead

import tickets.repository.worker_team as repo

router = APIRouter(prefix="/worker-teams", tags=["GlobalWorkerTeams"])

@router.post(
    "/",
    response_model=WorkerTeamRead,
    status_code=status.HTTP_201_CREATED,
)
def create_worker_team(
    payload: WorkerTeamCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_project_admin),
) -> WorkerTeamRead:
    raw = repo.create_worker_team(db, payload.name)
    return WorkerTeamRead.model_validate(raw)

@router.get(
    "/",
    response_model=List[WorkerTeamRead],
)
def list_worker_teams(
    db: Session = Depends(get_db),
    _current_user=Depends(require_project_admin),
) -> List[WorkerTeamRead]:
    raws = repo.list_worker_teams(db)
    return [WorkerTeamRead.model_validate(wt) for wt in raws]

@router.get(
    "/{wt_id}",
    response_model=WorkerTeamRead,
)
def read_worker_team(
    wt_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    _current_user=Depends(require_project_admin),
) -> WorkerTeamRead:
    raw = repo.get_worker_team_by_id(db, wt_id)
    if not raw:
        raise HTTPException(status_code=404, detail="WorkerTeam not found")
    return WorkerTeamRead.model_validate(raw)

@router.delete(
    "/{wt_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_worker_team(
    wt_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    _current_user=Depends(require_project_admin),
) -> Response:
    try:
        repo.delete_worker_team(db, wt_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="WorkerTeam not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
