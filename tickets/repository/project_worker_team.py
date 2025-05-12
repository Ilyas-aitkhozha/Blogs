# tickets/repository/project_worker_team.py

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from tickets.models import WorkerTeam, Project, User, UserTeam


def create_worker_team(
    db: Session,
    name: str,
    admin_id: int,
) -> WorkerTeam:
    wt = WorkerTeam(name=name, admin_id=admin_id)
    db.add(wt)
    db.commit()
    db.refresh(wt)
    return wt


def assign_worker_team_to_project(
    db: Session,
    project_id: int,
    worker_team_id: int,
) -> None:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    project.worker_team_id = worker_team_id
    db.commit()


def create_and_assign_worker_team(
    db: Session,
    project_id: int,
    name: str,
    admin_id: int,
) -> dict:
    # 1) создаём новую команду
    wt = create_worker_team(db, name, admin_id)
    # 2) привязываем её к проекту
    assign_worker_team_to_project(db, project_id, wt.id)
    # 3) собираем результат под ProjectWorkerTeamRead
    return {
        "id": wt.id,
        "project_id": project_id,
        "team_id": wt.id,
        "assigned_at": datetime.now(timezone.utc),
        "name": wt.name,
        "description": None,
    }


def update_worker_team_for_project(
    db: Session,
    project_id: int,
    new_worker_team_id: int,
) -> dict:
    # просто переиспользуем assign + собираем payload
    assign_worker_team_to_project(db, project_id, new_worker_team_id)
    wt = get_worker_team_of_project(db, project_id)
    return {
        "id": wt.id,
        "project_id": project_id,
        "team_id": wt.id,
        "assigned_at": datetime.now(timezone.utc),
        "name": wt.name,
        "description": None,
    }


def remove_worker_team_from_project(
    db: Session,
    project_id: int,
) -> None:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    project.worker_team_id = None
    db.commit()


def get_worker_team_of_project(
    db: Session,
    project_id: int,
) -> Optional[WorkerTeam]:
    project = db.query(Project).filter(Project.id == project_id).first()
    return project.worker_team if project else None


def list_projects_without_worker_team(
    db: Session,
) -> List[Project]:
    return db.query(Project).filter(Project.worker_team_id.is_(None)).all()


def list_worker_teams(
    db: Session,
) -> List[WorkerTeam]:
    return db.query(WorkerTeam).all()


def get_available_workers_by_project(
    db: Session,
    project_id: int,
) -> List[User]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or not project.worker_team:
        return []
    wt_id = project.worker_team.id
    return (
        db.query(User)
          .join(UserTeam, User.id == UserTeam.user_id)
          .filter(
              UserTeam.team_id == wt_id,
              User.is_available.is_(True),
          )
          .all()
    )
