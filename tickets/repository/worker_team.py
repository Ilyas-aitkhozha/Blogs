from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from tickets.models import WorkerTeam

def create_worker_team(
    db: Session,
    name: str,
) -> WorkerTeam:
    wt = WorkerTeam(
        name=name,
        created_at=datetime.now(timezone.utc),
    )
    db.add(wt)
    db.commit()
    db.refresh(wt)
    return wt

def get_worker_team_by_id(
    db: Session,
    wt_id: int,
) -> Optional[WorkerTeam]:
    return db.query(WorkerTeam).get(wt_id)

def list_worker_teams(
    db: Session,
) -> List[WorkerTeam]:
    return db.query(WorkerTeam).all()

def update_worker_team(
    db: Session,
    wt_id: int,
    name: str,
) -> WorkerTeam:
    wt = db.query(WorkerTeam).get(wt_id)
    if not wt:
        raise ValueError("WorkerTeam not found")
    wt.name = name
    db.commit()
    db.refresh(wt)
    return wt

def delete_worker_team(
    db: Session,
    wt_id: int,
) -> None:
    wt = db.query(WorkerTeam).get(wt_id)
    if not wt:
        raise ValueError("WorkerTeam not found")
    db.delete(wt)
    db.commit()