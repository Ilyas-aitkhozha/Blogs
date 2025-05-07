# routers/project.py
from typing import List
from fastapi import APIRouter, Depends, Path, Query, status, HTTPException, Response
from sqlalchemy.orm import Session
from ..enums import *
from tickets.database import get_db
from tickets.routers.dependencies import require_team_admin
from tickets.schemas.project import ProjectCreate, ProjectOut
from tickets.schemas.user import ShowUser
from tickets.repository import project as project_repo
from tickets.repository import user as user_repo
from tickets.enums import ProjectRole
from tickets.models import User

router = APIRouter(
    prefix="/teams/{team_id}/projects",
    tags=["Projects"]
)

@router.post(
    "/",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    project_in: ProjectCreate,
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_team_admin),
):
    if project_in.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team ID mismatch"
        )
    return project_repo.create_project(db, project_in,team_id, current_user.id)

@router.get(
    "/",
    response_model=List[ProjectOut],
)
def list_projects(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    return project_repo.get_projects_by_team(db, team_id)

@router.get(
    "/{project_id}",
    response_model=ProjectOut,
)
def get_project(
    team_id: int = Path(..., ge=1),
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    proj = project_repo.get_project_by_id(db, project_id)
    if proj.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in this team"
        )
    return proj

@router.post(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def add_user_to_project(
    project_id: int = Path(..., ge=1),
    user_id: int = Path(..., ge=1),
    role: ProjectRole = Query(ProjectRole.member),
    db: Session = Depends(get_db),
):
    project_repo.add_user_to_project(db, project_id, user_id, role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_user_from_project(
    project_id: int = Path(..., ge=1),
    user_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    project_repo.remove_user_from_project(db, project_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.get("/projects/{project_id}/assignees", response_model=List[ShowUser])
def list_assignees(
    project_id: int,
    ticket_type: TicketType,
    db: Session = Depends(get_db)
):
    if ticket_type == TicketType.worker:
        return user_repo.get_available_users_by_role(db, "worker", project_id)
    return user_repo.get_project_users_by_role(db, project_id,ProjectRole.member)
