from sqlalchemy.orm import Session
from tickets.models import Project
from tickets.schemas.project import ProjectCreate


def create_project(db: Session, project_in: ProjectCreate, user_id: int) -> Project:
    proj = Project(
        name=project_in.name,
        description=project_in.description,
        team_id=project_in.team_id,
        created_by=user_id
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


def get_projects_by_team(db: Session, team_id: int):
    return db.query(Project).filter(Project.team_id == team_id).all()