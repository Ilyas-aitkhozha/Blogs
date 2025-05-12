from sqlalchemy.orm import Session
from typing import List, Optional
from tickets.models import WorkerTeam, Project, User, UserTeam

def create_worker_team(
    db: Session,
    name: str,
    admin_id: int,
) -> WorkerTeam:
    wt = WorkerTeam(
        name=name,
        admin_id=admin_id,
    )
    db.add(wt)
    db.commit()
    db.refresh(wt)
    return wt

# Assign an existing worker's team to a project (one per project)
def assign_worker_team_to_project(
    db: Session,
    project_id: int,
    worker_team_id: int,
) -> Project:
    project = db.query(Project).get(project_id)
    if not project:
        raise ValueError("Project not found")
    project.worker_team_id = worker_team_id
    db.commit()
    db.refresh(project)
    return project

# Update or reassign the worker's team for a project
def update_worker_team_for_project(
    db: Session,
    project_id: int,
    new_worker_team_id: int,
) -> Project:
    return assign_worker_team_to_project(db, project_id, new_worker_team_id)

# Remove the worker's team assignment from a project
def remove_worker_team_from_project(
    db: Session,
    project_id: int,
) -> Project:
    project = db.query(Project).get(project_id)
    if not project:
        raise ValueError("Project not found")
    project.worker_team_id = None
    db.commit()
    db.refresh(project)
    return project

# Get the worker's team assigned to a project
def get_worker_team_of_project(
    db: Session,
    project_id: int,
) -> Optional[WorkerTeam]:
    project = db.query(Project).get(project_id)
    return project.worker_team if project else None

# List all projects without any worker's team assigned
def list_projects_without_worker_team(
    db: Session,
) -> List[Project]:
    return (
        db.query(Project)
          .filter(Project.worker_team_id.is_(None))
          .all()
    )

# List all existing worker's teams
def list_worker_teams(
    db: Session,
) -> List[WorkerTeam]:
    return db.query(WorkerTeam).all()

# Get available users (is_available=True) in the project's worker team
def get_available_workers_by_project(
    db: Session,
    project_id: int,
) -> List[User]:
    project = db.query(Project).get(project_id)
    if not project or not project.worker_team:
        return []
    wt = project.worker_team
    return (
        db.query(User)
          .join(UserTeam, User.id == UserTeam.user_id)
          .filter(
              UserTeam.team_id == wt.id,
              User.is_available.is_(True),
          )
          .all()
    )
