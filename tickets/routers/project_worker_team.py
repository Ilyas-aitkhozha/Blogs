from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response, Path
from sqlalchemy.orm import Session
from typing import List

from tickets.database import get_db
from tickets.routers.dependencies import require_project_admin, require_project_member, require_team_admin
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
def create_worker_team(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    data: ProjectWorkerTeamCreate = ...,
    db: Session = Depends(get_db),
    current_user=Depends(require_team_admin),
) -> ProjectWorkerTeamRead:
    """
    Создаёт новую worker-team и привязывает её к проекту.
    """
    result = repo.create_and_assign_worker_team(
        db=db,
        project_id=project_id,
        name=data.name,
        admin_id=current_user.id,
    )
    return ProjectWorkerTeamRead.model_validate(result)

@router.post(
    "/assign",
    response_model=ProjectWorkerTeamRead,
    status_code=status.HTTP_201_CREATED,
)
def assign_team(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_project_admin),
) -> ProjectWorkerTeamRead:
    """
    Назначить существующую worker-team к проекту.
    """
    repo.assign_worker_team_to_project(db, project_id, team_id)
    wt = repo.get_worker_team_of_project(db, project_id)
    if not wt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker-team not found after assignment")
    result = {
        "id": wt.id,
        "project_id": project_id,
        "team_id": wt.id,
        "assigned_at": datetime.now(timezone.utc),
        "name": wt.name,
        "description": None,
    }
    return ProjectWorkerTeamRead.model_validate(result)

@router.get(
    "/",
    response_model=ProjectWorkerTeamRead,
)
def read_team(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_project_member),
) -> ProjectWorkerTeamRead:
    """
    Получить информацию о текущей worker-team проекта.
    """
    wt = repo.get_worker_team_of_project(db, project_id)
    if not wt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No worker-team assigned to this project")
    result = {
        "id": wt.id,
        "project_id": project_id,
        "team_id": wt.id,
        "assigned_at": datetime.now(timezone.utc),
        "name": wt.name,
        "description": None,
    }
    return ProjectWorkerTeamRead.model_validate(result)

@router.patch(
    "/",
    response_model=ProjectWorkerTeamRead,
)
def reassign_team(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_project_admin),
) -> ProjectWorkerTeamRead:
    """
    Переназначить worker-team проекта.
    """
    repo.update_worker_team_for_project(db, project_id, team_id)
    wt = repo.get_worker_team_of_project(db, project_id)
    result = {
        "id": wt.id,
        "project_id": project_id,
        "team_id": wt.id,
        "assigned_at": datetime.now(timezone.utc),
        "name": wt.name,
        "description": None,
    }
    return ProjectWorkerTeamRead.model_validate(result)

@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unassign_team(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_project_admin),
) -> None:
    """
    Снять назначение worker-team с проекта.
    """
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
    """
    Список доступных пользователей в worker-team проекта.
    """
    users = repo.get_available_workers_by_project(db, project_id)
    return [UserBrief.model_validate(u) for u in users]

@router.get(
    "/available",
    response_model=List[TeamBriefInfo],
)
def list_free_teams(
    db: Session = Depends(get_db),
    current_user=Depends(require_project_member),
) -> List[TeamBriefInfo]:
    """
    Список всех существующих worker-teams.
    """
    teams = repo.list_worker_teams(db)
    return [TeamBriefInfo.model_validate(t) for t in teams]

@router.get(
    "/unassigned-projects",
    response_model=List[ProjectBrief],
)
def list_projects_needing_team(
    db: Session = Depends(get_db),
    current_user=Depends(require_project_admin),
) -> List[ProjectBrief]:
    """
    Список проектов без назначенной worker-team.
    """
    projects = repo.list_projects_without_worker_team(db)
    return [ProjectBrief.model_validate(p) for p in projects]
