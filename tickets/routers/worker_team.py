from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import List
from tickets.database import get_db
from tickets.routers.dependencies import require_team_admin, require_team_member
from tickets.schemas.worker_team import WorkerTeamCreate, WorkerTeamRead
import tickets.repository.worker_team as repo

router = APIRouter(
    prefix="/teams/{team_id}/worker-teams",
    tags=["Worker Teams"],
)


@router.post(
    "/",
    response_model=WorkerTeamRead,
    status_code=status.HTTP_201_CREATED,
)
def create_worker_team(
    team_id: int = Path(..., ge=1),
    data: WorkerTeamCreate = ...,
    db: Session = Depends(get_db),
    current_user=Depends(require_team_admin),
) -> WorkerTeamRead:
    wt = repo.create_worker_team(db, team_id, data.name, current_user.id)
    return wt

@router.get(
    "/",
    response_model=List[WorkerTeamRead],
)
def list_worker_teams(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_team_member),
) -> List[WorkerTeamRead]:
    """
    Получить все WorkerTeam для Team(team_id).
    """
    return repo.list_worker_teams(db, team_id)

@router.get(
    "/{worker_team_id}",
    response_model=WorkerTeamRead,
)
def get_worker_team(
    team_id: int = Path(..., ge=1),
    worker_team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_team_member),
) -> WorkerTeamRead:
    wt = repo.get_worker_team(db, team_id, worker_team_id)
    if not wt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="WorkerTeam not found",
        )
    return wt
