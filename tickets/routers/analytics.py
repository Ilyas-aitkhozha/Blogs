from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
import io
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..database import get_db
from .. import models

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def compute_team_metrics(team_id: int, db: Session) -> Dict:
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

    status_summary = (
        df["status"].value_counts().sort_index().to_dict()
    )

    #Workload (assignee)
    total_tickets = len(df)
    workload = (
        df.groupby(["assignee_id", "assignee_name"])  # assignee_id может быть NaN
        .size()
        .reset_index(name="count")
    )
    workload["percent"] = (workload["count"] / total_tickets * 100).round(0).astype(int)
    workload_dict = [
        {
            "assignee_id": int(a) if pd.notna(a) else None,
            "assignee_name": n if pd.notna(n) else "Unassigned",
            "count": int(c),
            "percent": int(p),
        }
        for a, n, c, p in workload.itertuples(index=False)
    ]

    return {
        "team_id": team_id,
        "total": total_tickets,
        "status_summary": status_summary,
        "workload": workload_dict,
    }


@router.get("/teams/{team_id}/metrics", response_model=Dict)
def team_metrics(team_id: int, db: Session = Depends(get_db)):
    """JSON сводка для дашборда и бота."""
    return compute_team_metrics(team_id, db)


@router.get(
    "/teams/{team_id}/status-pie",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}},
)
def status_pie(team_id: int, db: Session = Depends(get_db)):
    """PNG‑пирог по статусам (для вставки в чат)."""
    metrics = compute_team_metrics(team_id, db)
    status_counts = metrics["status_summary"]

    # График
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(
        status_counts.values(),
        labels=status_counts.keys(),
        autopct="%1.0f%%",
        startangle=90,
    )
    ax.set_title("Status summary")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")
