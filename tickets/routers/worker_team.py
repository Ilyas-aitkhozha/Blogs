from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List

from tickets.database import get_db
from tickets.schemas.worker_team import WorkerTeamCreate, WorkerTeamRead
import tickets.repository.worker_team as repo
from tickets.routers.dependencies import require_project_admin

router = APIRouter(prefix="/worker-teams", tags=["WorkerTeams"])

@router.post("/", response_model=WorkerTeamRead, status_code=status.HTTP_201_CREATED)
def create_worker_team(
    payload: WorkerTeamCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_project_admin),  # limit creation if needed
):
    wt = repo.create_worker_team(db, payload.name)
    return wt

@router.get("/", response_model=List[WorkerTeamRead])
def list_worker_teams(
    db: Session = Depends(get_db),
):
    return repo.list_worker_teams(db)

@router.get("/{wt_id}", response_model=WorkerTeamRead)
def read_worker_team(
    wt_id: int,
    db: Session = Depends(get_db),
):
    wt = repo.get_worker_team_by_id(db, wt_id)
    if not wt:
        raise HTTPException(status_code=404, detail="WorkerTeam not found")
    return wt

@router.delete("/{wt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worker_team(
    wt_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_project_admin),
):
    try:
        repo.delete_worker_team(db, wt_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="WorkerTeam not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)