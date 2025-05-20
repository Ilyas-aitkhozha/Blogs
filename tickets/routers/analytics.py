from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict
import pandas as pd

from ..database import get_db
from .. import models

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def compute_team_metrics(team_id: int, db: Session) -> Dict[str, Any]:
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

    q = (
        db.query(
            models.Ticket.status.label("status"),
            models.Ticket.assigned_to.label("assignee_id"),
            models.User.name.label("assignee_name")
        )
        .outerjoin(models.User, models.User.id == models.Ticket.assigned_to)
        .filter(models.Ticket.team_id == team_id)
    )
    df = pd.read_sql(q.statement, db.bind)

    status_summary = df["status"].value_counts().sort_index().to_dict()

    total_tickets = len(df)
    workload_df = (
        df
        .groupby(["assignee_id", "assignee_name"])
        .size()
        .reset_index(name="count")
    )
    workload_df["percent"] = (workload_df["count"] / total_tickets * 100).round(0).astype(int)

    workload = []
    for row in workload_df.itertuples(index=False):
        workload.append({
            "assignee_id": int(row.assignee_id) if pd.notna(row.assignee_id) else None,
            "assignee_name": row.assignee_name or "Unassigned",
            "count": int(row.count),
            "percent": int(row.percent),
        })

    return {
        "team_id": team_id,
        "total_tickets": total_tickets,
        "status_summary": status_summary,
        "workload": workload,
    }


@router.get("/teams/{team_id}/metrics", response_model=Dict[str, Any])
def team_metrics(team_id: int, db: Session = Depends(get_db)):
    return compute_team_metrics(team_id, db)
