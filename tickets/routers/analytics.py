from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/analytics", tags=["Analytics"])



def _query_tickets(team_id: int, db: Session):
    q = (
        db.query(
            models.Ticket.id,
            models.Ticket.status.label("status"),
            models.Ticket.priority.label("priority"),
            models.Ticket.created_at.label("created_at"),
            models.Ticket.closed_at.label("closed_at"),
            models.Ticket.assigned_to.label("assignee_id"),
            models.User.name.label("assignee_name"),
        )
        .outerjoin(models.User, models.User.id == models.Ticket.assigned_to)
        .filter(models.Ticket.team_id == team_id)
    )
    return pd.read_sql(q.statement, db.bind)



def compute_team_metrics(team_id: int, db: Session) -> Dict[str, Any]:
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

    df = _query_tickets(team_id, db)
    if df.empty:
        return {
            "team_id": team_id,
            "total_tickets": 0,
            "status_summary": {},
            "workload": [],
        }

    status_summary = df["status"].value_counts().sort_index().to_dict()

    total_tickets = len(df)
    workload_df = (
        df.groupby(["assignee_id", "assignee_name"])
        .size()
        .reset_index(name="count")
    )
    workload_df["percent"] = (workload_df["count"] / total_tickets * 100).round(0).astype(int)

    workload: List[Dict[str, Any]] = []
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



def compute_resolution_metrics(team_id: int, db: Session) -> Dict[str, Any]:
    df = _query_tickets(team_id, db)
    df = df[(df["status"] == "closed") & pd.notna(df["closed_at"])]
    if df.empty:
        return {"team_id": team_id, "average_hours": None, "median_hours": None, "per_assignee": []}

    df["resolution_hours"] = (df["closed_at"] - df["created_at"]).dt.total_seconds() / 3600

    overall_avg = round(df["resolution_hours"].mean(), 1)
    overall_median = round(df["resolution_hours"].median(), 1)

    assignee_df = (
        df.groupby(["assignee_id", "assignee_name"])["resolution_hours"]
        .agg(["mean", "median", "count"])
        .reset_index()
    )

    per_assignee: List[Dict[str, Any]] = []
    for row in assignee_df.itertuples(index=False):
        per_assignee.append({
            "assignee_id": int(row.assignee_id) if pd.notna(row.assignee_id) else None,
            "assignee_name": row.assignee_name or "Unassigned",
            "avg_hours": round(row.mean, 1),
            "median_hours": round(row.median, 1),
            "closed_count": int(row.count),
        })

    return {
        "team_id": team_id,
        "average_hours": overall_avg,
        "median_hours": overall_median,
        "per_assignee": per_assignee,
    }



def compute_ticket_trend(team_id: int, db: Session, days: int) -> List[Dict[str, Any]]:
    df = _query_tickets(team_id, db)
    if df.empty:
        return []

    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=days - 1)

    opened = (
        df["created_at"].dropna().dt.date.value_counts().rename_axis("date").sort_index()
    )
    closed = (
        df[df["status"] == "closed"]["closed_at"].dropna().dt.date.value_counts().rename_axis("date").sort_index()
    )

    all_dates = pd.date_range(start=start_date, end=today, freq="D").date

    trend: List[Dict[str, Any]] = []
    for d in all_dates:
        trend.append({
            "date": d.isoformat(),
            "opened": int(opened.get(d, 0)),
            "closed": int(closed.get(d, 0)),
        })
    return trend


_SLA_THRESHOLDS_HOURS = {
    "urgent": 24,
    "high": 48,
    "medium": 72,
    "low": 168,
}


def compute_sla_metrics(team_id: int, db: Session) -> Dict[str, Any]:
    df = _query_tickets(team_id, db)
    df = df[(df["status"] == "closed") & pd.notna(df["closed_at"]) & pd.notna(df["priority"])]
    if df.empty:
        return {"team_id": team_id, "sla_compliance": {}}

    df["resolution_hours"] = (df["closed_at"] - df["created_at"]).dt.total_seconds() / 3600

    result: Dict[str, Dict[str, Any]] = {}
    for pr, hours in _SLA_THRESHOLDS_HOURS.items():
        subset = df[df["priority"] == pr]
        if subset.empty:
            continue
        within = (subset["resolution_hours"] <= hours).sum()
        total = len(subset)
        percent = round(within / total * 100, 1)
        result[pr] = {"total": total, "within_sla": within, "percent": percent}

    return {"team_id": team_id, "sla_compliance": result}

#routers
@router.get("/teams/{team_id}/metrics", response_model=Dict[str, Any])
async def team_metrics(team_id: int, db: Session = Depends(get_db)):
    return compute_team_metrics(team_id, db)


@router.get("/teams/{team_id}/resolution-metrics", response_model=Dict[str, Any])
async def resolution_metrics(team_id: int, db: Session = Depends(get_db)):
    return compute_resolution_metrics(team_id, db)

@router.get("/teams/{team_id}/trend", response_model=List[Dict[str, Any]])
async def ticket_trend(
    team_id: int,
    days: int = Query(30, ge=1, le=365, description="Период в днях"),
    db: Session = Depends(get_db),
):
    return compute_ticket_trend(team_id, db, days)


@router.get("/teams/{team_id}/sla-metrics", response_model=Dict[str, Any])
async def sla_metrics(team_id: int, db: Session = Depends(get_db)):
    return compute_sla_metrics(team_id, db)
