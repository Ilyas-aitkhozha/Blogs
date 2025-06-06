from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from tickets.models import WorkerTeam, Project, User, UserTeam, WorkerTeamMember
from tickets.enums import WorkerRole
from tickets.repository.project import ensure_users_in_team

# CREATE WORKER TEAM

def create_worker_team(
    db: Session,
    team_id: int,
    name: str,
    admin_id: int,
) -> WorkerTeam:
    # Проверяем, что админ состоит в команде
    ensure_users_in_team(db, team_id, [admin_id])

    wt = WorkerTeam(
        team_id=team_id,
        name=name,
        description=None
    )
    db.add(wt)
    db.commit()
    db.refresh(wt)

    admin_link = WorkerTeamMember(
        worker_team_id=wt.id,
        user_id=admin_id,
        role=WorkerRole.admin,
        joined_at=datetime.now(timezone.utc)
    )
    db.add(admin_link)
    db.commit()
    return wt

# ASSIGN LOGIC

def assign_worker_team_to_project(
    db: Session,
    project_id: int,
    worker_team_id: int,
    current_user_id: int
) -> None:
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверяем, что current_user состоит в команде проекта
    ensure_users_in_team(db, project.team_id, [current_user_id])

    wt = db.query(WorkerTeam).filter_by(id=worker_team_id).first()
    if not wt or wt.team_id != project.team_id:
        raise HTTPException(status_code=404,
                            detail="WorkerTeam not found in this Team")

    project.worker_team_id = wt.id
    db.commit()


def create_and_assign_worker_team(
    db: Session,
    team_id: int,
    project_id: int,
    name: str,
    admin_id: int,
    current_user_id: int,
) -> dict:
    # Проверяем, что current_user состоит в команде и админ состоит в команде
    ensure_users_in_team(db, team_id, [current_user_id, admin_id])

    wt = create_worker_team(db, team_id, name, admin_id)
    assign_worker_team_to_project(db, project_id, wt.id, current_user_id)
    return {
        "id": wt.id,
        "project_id": project_id,
        "team_id": wt.id,
        "assigned_at": datetime.now(timezone.utc),
        "name": wt.name,
        "description": None,
    }

# MEMBERSHIP LOGIC

def add_member_to_worker_team(
    db: Session,
    worker_team_id: int,
    user_id: int,
    current_user_id: int
):
    wt = db.query(WorkerTeam).filter_by(id=worker_team_id).first()
    if not wt:
        raise HTTPException(status_code=404, detail="WorkerTeam not found")

    # Проверяем, что current_user и целевой пользователь состоят в команде
    ensure_users_in_team(db, wt.team_id, [current_user_id, user_id])

    exists = (
        db.query(WorkerTeamMember)
          .filter_by(worker_team_id=worker_team_id, user_id=user_id)
          .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="User already in WorkerTeam")

    link = WorkerTeamMember(worker_team_id=worker_team_id, user_id=user_id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def remove_user_from_worker_team(
    db: Session,
    worker_team_id: int,
    user_id: int,
    current_user_id: int
) -> None:
    wt = db.query(WorkerTeam).filter_by(id=worker_team_id).first()
    if not wt:
        raise HTTPException(status_code=404, detail="WorkerTeam not found")

    # Проверяем, что current_user состоит в команде
    ensure_users_in_team(db, wt.team_id, [current_user_id])

    deleted = (
        db.query(WorkerTeamMember)
          .filter_by(worker_team_id=worker_team_id, user_id=user_id)
          .delete()
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not in this worker_team"
        )
    db.commit()

# LIST & GET LOGICS (без изменений)

def update_worker_team_for_project(
    db: Session,
    project_id: int,
    new_worker_team_id: int,
    current_user_id: int
) -> dict:
    assign_worker_team_to_project(db, project_id, new_worker_team_id, current_user_id)
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
    current_user_id: int
) -> None:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Проверяем, что current_user состоит в команде проекта
    ensure_users_in_team(db, project.team_id, [current_user_id])

    project.worker_team_id = None
    db.commit()


def list_projects_without_worker_team(
    db: Session,
) -> List[Project]:
    return db.query(Project).filter(Project.worker_team_id.is_(None)).all()


def list_worker_teams(
    db: Session,
) -> List[WorkerTeam]:
    return db.query(WorkerTeam).all()


def get_worker_team_of_project(
    db: Session,
    project_id: int,
) -> Optional[WorkerTeam]:
    project = db.query(Project).filter(Project.id == project_id).first()
    return project.worker_team if project else None


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


def get_available_workers_by_worker_team(db: Session, worker_team_id: int) -> List[User]:
    return (
        db.query(User)
          .join(WorkerTeamMember, User.id == WorkerTeamMember.user_id)
          .filter(
              WorkerTeamMember.worker_team_id == worker_team_id,
              User.is_available.is_(True),
          )
          .all()
    )

def get_all_available_workers(db: Session) -> List[User]:
    return db.query(User).filter(User.is_available.is_(True)).all()
