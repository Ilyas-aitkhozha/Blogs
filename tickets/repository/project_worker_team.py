from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import List, Optional
from tickets.models import ProjectWorkerTeam, Project, Team, User, UserTeam
# only 1 workers team to one project
def assign_worker_team(
    db: Session, project_id: int, team_id: int
) -> ProjectWorkerTeam:
    existing = (
        db.query(ProjectWorkerTeam)
          .filter_by(project_id=project_id)
          .first()
    )
    if existing:
        raise ValueError("Project already has a worker team")

    link = ProjectWorkerTeam(
        project_id=project_id,
        team_id=team_id,
        assigned_at=datetime.now(timezone.utc),
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def update_worker_team(
    db: Session, project_id: int, new_team_id: int
) -> ProjectWorkerTeam:
    link = (
        db.query(ProjectWorkerTeam)
          .filter_by(project_id=project_id)
          .first()
    )
    if not link:
        raise ValueError("No existing worker team to update")

    link.team_id = new_team_id
    link.assigned_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(link)
    return link


def remove_worker_team(db: Session, project_id: int) -> None:
    link = (
        db.query(ProjectWorkerTeam)
          .filter_by(project_id=project_id)
          .first()
    )
    if link:
        db.delete(link)
        db.commit()


def get_worker_team(
    db: Session, project_id: int
) -> Optional[ProjectWorkerTeam]:
    return (
        db.query(ProjectWorkerTeam)
          .filter_by(project_id=project_id)
          .first()
    )


def list_unassigned_projects(db: Session) -> List[Project]:
    # all project_ids that already have a worker-team
    assigned_ids = db.query(ProjectWorkerTeam.project_id)
    # select projects whose id is not in that list
    return (
        db.query(Project)
          .filter(~Project.id.in_(assigned_ids))
          .all()
    )


# teams that don’t have any projects assigned to them
def list_available_worker_teams(db: Session) -> List[Team]:
    assigned_ids = db.query(ProjectWorkerTeam.team_id)
    return (
        db.query(Team)
          .filter(~Team.id.in_(assigned_ids))
          .all()
    )


def get_available_workers_by_project(
    db: Session, project_id: int
) -> List[User]:
    link = get_worker_team(db, project_id)
    if not link:
        return []

    return (
        db.query(User)
          .join(UserTeam, User.id == UserTeam.user_id)
          .filter(
              UserTeam.team_id == link.team_id,
              User.is_available.is_(True),
          )
          .all()
    )