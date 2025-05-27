from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from tickets.schemas.user import UserBrief
from tickets.models import Project, ProjectUser, User, UserTeam
from tickets.schemas.project import ProjectCreate
from tickets.enums import ProjectRole

#---------------- helper
def ensure_users_in_team(
     db: Session,
     team_id: int,
     user_ids: list[int]
 ) -> None:
     rows = (
         db.query(UserTeam.user_id)
           .filter(
               UserTeam.team_id == team_id,
               UserTeam.user_id.in_(user_ids)
           )
           .distinct()
           .all()
     )
     found_ids = {uid for (uid,) in rows}
     missing = set(user_ids) - found_ids
     if missing:
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail=f"Users {sorted(missing)} are not members of team {team_id}"
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


def get_users_in_project(db: Session, project_id: int, current_user_id: int) -> List[UserBrief]:
    # проверяем, что current_user состоит в команде проекта
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    ensure_users_in_team(db, proj.team_id, [current_user_id])
    users = (
        db.query(User)
          .join(ProjectUser, User.id == ProjectUser.user_id)
          .filter(ProjectUser.project_id == project_id)
          .all()
    )
    return [UserBrief.model_validate(u) for u in users]

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
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    team_id = project.team_id
    ensure_users_in_team(db, team_id, [current_user_id, user_id])
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
    user_id: int,
    current_user_id: int
) -> None:
    proj = get_project_by_id(db, project_id)
    ensure_users_in_team(db, proj.team_id, [current_user_id])

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
