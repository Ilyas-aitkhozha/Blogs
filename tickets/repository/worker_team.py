from sqlalchemy.orm import Session
from tickets.models import WorkerTeam

def create_worker_team(
    db: Session,
    team_id: int,
    name: str,
    admin_id: int,
) -> WorkerTeam:
    wt = WorkerTeam(
        team_id=team_id,
        name=name,
        admin_id=admin_id,
    )
    db.add(wt)
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
