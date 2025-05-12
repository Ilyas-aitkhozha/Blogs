from sqlalchemy.orm import Session
from tickets.models import WorkerTeam
from fastapi import HTTPException, status
from tickets.models import Team, WorkerTeam

def create_worker_team(
    db: Session,
    team_id: int,
    name: str,
    admin_id: int,
) -> WorkerTeam:
    team = db.query(Team).filter_by(id=team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Team not found")
    wt = WorkerTeam(name=name, admin_id=admin_id)
    team.worker_teams.append(wt)
    db.commit()
    db.refresh(wt)
    return wt

def list_worker_teams(
    db: Session,
    team_id: int,
) -> list[WorkerTeam]:
    return db.query(WorkerTeam).filter_by(team_id=team_id).all()

def get_worker_team(
    db: Session,
    team_id: int,
    worker_team_id: int,
) -> WorkerTeam | None:
    return (
        db.query(WorkerTeam)
          .filter_by(team_id=team_id, id=worker_team_id)
          .first()
    )
