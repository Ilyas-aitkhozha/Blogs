from datetime import datetime, timezone
from sqlalchemy.orm import Session
from tickets.models import ProjectWorkerTeam, Project, Team, User, UserTeam
#only 1 workers team to one project
def assign_worker_team(db: Session, project_id: int, team_id: int) -> ProjectWorkerTeam:
    existing = db.query(ProjectWorkerTeam).filter_by(project_id=project_id).first()
    if existing:
        raise ValueError("Project already has a worker team")
    link = ProjectWorkerTeam(
        project_id=project_id,
        team_id=team_id,
        assigned_at=datetime.now(timezone.utc)
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link