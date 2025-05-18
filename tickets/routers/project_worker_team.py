from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import List
from tickets.schemas.worker_team_member import WorkerTeamMemberRead
from tickets.schemas.worker_team import WorkerTeamBrief
from tickets.database import get_db
from tickets.routers.dependencies import (
    require_project_admin,
    require_project_member,
    require_team_admin,
)
from tickets.schemas.project_worker_team import (
    ProjectWorkerTeamCreate,
    ProjectWorkerTeamRead,
)
from tickets.schemas.project import ProjectBrief
from tickets.schemas.team import TeamBriefInfo
from tickets.schemas.user import UserBrief
import tickets.repository.project_worker_team as repo

router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}/worker-team",
    tags=["Worker Teams"],
)


@router.post(
    "/create",
    response_model=ProjectWorkerTeamRead,
    status_code=status.HTTP_201_CREATED,
)
def create_and_assign_worker_team(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    data: ProjectWorkerTeamCreate = ...,
    db: Session = Depends(get_db),
    current_user=Depends(require_team_admin),
) -> ProjectWorkerTeamRead:
    result = repo.create_and_assign_worker_team(
        team_id=team_id,
        db=db,
        project_id=project_id,
        name=data.name,
        admin_id=current_user.id,
    )
    return ProjectWorkerTeamRead.model_validate(result)


@router.post(
    "/assign/{worker_team_id}",
    response_model=ProjectWorkerTeamRead,
    status_code=status.HTTP_200_OK,
)
def assign_existing_worker_team(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    worker_team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_project_admin),
) -> ProjectWorkerTeamRead:
    repo.assign_worker_team_to_project(db, project_id, worker_team_id)
    wt = repo.get_worker_team_of_project(db, project_id)
    payload = {
        "id": wt.id,
        "project_id": project_id,
        "team_id": wt.id,
        "assigned_at": datetime.now(timezone.utc),
        "name": wt.name,
        "description": None,
    }
    return ProjectWorkerTeamRead.model_validate(payload)


@router.get(
    "/",
    response_model=ProjectWorkerTeamRead,
)
def read_worker_team_assignment(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_project_member),
) -> ProjectWorkerTeamRead:
    wt = repo.get_worker_team_of_project(db, project_id)
    if not wt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No WorkerTeam assigned")
    payload = {
        "id": wt.id,
        "project_id": project_id,
        "team_id": wt.id,
        "assigned_at": datetime.now(timezone.utc),
        "name": wt.name,
        "description": None,
    }
    return ProjectWorkerTeamRead.model_validate(payload)


@router.patch(
    "/reassign/{worker_team_id}",
    response_model=ProjectWorkerTeamRead,
)
def reassign_worker_team(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    worker_team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_project_admin),
) -> ProjectWorkerTeamRead:
    repo.update_worker_team_for_project(db, project_id, worker_team_id)
    wt = repo.get_worker_team_of_project(db, project_id)
    payload = {
        "id": wt.id,
        "project_id": project_id,
        "team_id": wt.id,
        "assigned_at": datetime.now(timezone.utc),
        "name": wt.name,
        "description": None,
    }
    return ProjectWorkerTeamRead.model_validate(payload)


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unassign_worker_team(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_project_admin),
) -> None:
    repo.remove_worker_team_from_project(db, project_id)


@router.get(
    "/available-workers",
    response_model=List[UserBrief],
)
def available_workers(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_project_member),
) -> List[UserBrief]:
    users = repo.get_available_workers_by_project(db, project_id)
    return [UserBrief.model_validate(u) for u in users]

@router.get(
    "/available",
    response_model=List[WorkerTeamBrief],
)
def list_all_worker_teams(
    db: Session = Depends(get_db),
    current_user=Depends(require_project_member),
) -> List[WorkerTeamBrief]:
    teams = repo.list_worker_teams(db)
    return [WorkerTeamBrief.model_validate(t) for t in teams]

@router.get(
    "/teams/{team_id}/worker-teams/{worker_team_id}/available-workers",
    response_model=List[UserBrief]
)
def available_workers_in_worker_team(
    team_id: int = Path(..., ge=1),
    worker_team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_project_member),
) -> List[UserBrief]:
    users = repo.get_available_workers_by_worker_team(db, worker_team_id)
    return [UserBrief.model_validate(u) for u in users]

@router.get(
    "/unassigned-projects",
    response_model=List[ProjectBrief],
)
def list_projects_needing_team(
    db: Session = Depends(get_db),
    current_user=Depends(require_project_admin),
) -> List[ProjectBrief]:
    projects = repo.list_projects_without_worker_team(db)
    return [ProjectBrief.model_validate(p) for p in projects]

@router.post(
    "/members/{user_id}",
    response_model=WorkerTeamMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    user_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_project_admin),
):
    # получаем worker_team_id от проекта
    wt = repo.get_worker_team_of_project(db, project_id)
    if not wt:
        raise HTTPException(status_code=404, detail="Project has no WorkerTeam")
    member = repo.add_member_to_worker_team(db, wt.id, user_id)
    return WorkerTeamMemberRead.model_validate(member)
