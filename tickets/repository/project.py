# repository/project_repository.py

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from tickets.models import Project, ProjectUser, User, UserTeam
from tickets.schemas.project import ProjectCreate
from tickets.enums import ProjectRole
#---------------- helper
def ensure_user_in_project_team(
    db: Session,
    project_id: int,
    user_id: int
) -> None:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    membership = (
        db.query(UserTeam)
          .filter(
            UserTeam.team_id == project.team_id,
            UserTeam.user_id == user_id
          )
          .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of the team to perform this action"
        )
#--------------------------------- CREATE LOGICS

def create_project(
    db: Session,
    project_in: ProjectCreate,
    team_id: int,
    user_id: int
) -> Project:
    proj = Project(
        name=project_in.name,
        description=project_in.description,
        team_id=team_id,
        created_by=user_id
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    association = ProjectUser(
        user_id=user_id,
        project_id=proj.id,
        role=ProjectRole.admin # when creating, instantly i give admin, idk if its good, but will see in future
    )
    db.add(association)
    db.commit()

    db.refresh(proj)
    return proj

#------------------------------ GET LOGICS

def get_projects_by_team(
    db: Session,
    team_id: int
) -> List[Project]:
    return db.query(Project).filter(Project.team_id == team_id).all()

def get_project_by_id(
    db: Session,
    project_id: int
) -> Project:
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    return proj

def get_projects_for_user(
    db: Session,
    user_id: int
) -> List[Project]:
    return (
        db.query(Project)
          .join(ProjectUser, ProjectUser.project_id == Project.id)
          .filter(ProjectUser.user_id == user_id)
          .all()
    )

#------------------------ MEMBERSHIP LOGICS

def add_user_to_project(
    db: Session,
    project_id: int,
    user_id: int,
    role: ProjectRole,
    current_user_id: int
) -> None:
    ensure_user_in_project_team(db, project_id, current_user_id)
    try:
        link = ProjectUser(
            project_id=project_id,
            user_id=user_id,
            role=role.value
        )
        db.add(link)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already in project"
        )

def remove_user_from_project(
    db: Session,
    project_id: int,
    user_id: int
) -> None:
    deleted = (
        db.query(ProjectUser)
          .filter_by(project_id=project_id, user_id=user_id)
          .delete()
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not in this project"
        )
    db.commit()

def get_project_members(
    db: Session,
    project_id: int,
    role: Optional[ProjectRole] = None
) -> List[User]:
    q = (
        db.query(User)
          .join(ProjectUser, ProjectUser.user_id == User.id)
          .filter(ProjectUser.project_id == project_id)
    )
    if role:
        q = q.filter(ProjectUser.role == role.value)
    return q.all()
