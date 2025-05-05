from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from tickets.database import get_db
from tickets.schemas.project import ProjectCreate, ProjectOut
from tickets.repository.project import create_project
from tickets.routers.dependencies import require_superadmin
from tickets.oauth2 import get_current_user
from tickets.models import User, Project

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/", response_model=ProjectOut)
async def create_new_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    return create_project(db, project, current_user.id)

@router.get("/", response_model=list[ProjectOut])
async def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "superadmin":
        return db.query(Project).all()
    return db.query(Project).filter(Project.created_by == current_user.id).all()