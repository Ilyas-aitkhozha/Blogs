from typing import List
import logging
from fastapi import APIRouter, Depends, HTTPException, Path, status, Body
from sqlalchemy.orm import Session
from tickets.database import get_db
from tickets.oauth2 import get_current_user
from tickets.schemas.ticket import TicketCreate, TicketStatusUpdate, TicketAssigneeUpdate, TicketOut, TicketFeedbackUpdate, TicketPriority
from tickets.repository import ticket as ticket_repo
from tickets import models
from ..enums import *

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/teams/{team_id}",
    tags=["Team Tickets"],
)

#helper
def _ensure_project_member(user, project_id: int):
    if not any(pu.project_id == project_id for pu in user.project_users):
        raise HTTPException(403, "Not a project member")

def _ensure_project_admin(user, project_id: int):
    if not any(pu.project_id == project_id and pu.role == ProjectRole.admin
               for pu in user.project_users):
        raise HTTPException(403, "Not a project admin")


@router.post("/tickets", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    project_id: int = Path(..., ge=1),
    payload: TicketCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_project_member(current_user, project_id)
    return ticket_repo.create_ticket(db, payload, current_user.id, project_id)



@router.get("/tickets", response_model=List[TicketOut])
def list_tickets(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_project_admin(current_user, project_id)
    return ticket_repo.get_all_tickets(db, project_id)


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(
    project_id: int,
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_project_member(current_user, project_id)
    return ticket_repo.get_ticket_by_id(db, ticket_id, project_id)


@router.get("/tickets/my-created", response_model=List[TicketOut])
def my_created(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_project_member(current_user, project_id)
    return ticket_repo.get_tickets_assigned_to_user(db, current_user, project_id)


@router.get("/tickets/my-assigned", response_model=List[TicketOut])
def my_assigned(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_membership(current_user, team_id)
    return ticket_repo.get_tickets_assigned_to_user(db, current_user, team_id)

@router.get("/tickets/priorities", response_model=list[str])
def get_priorities():
    return [p.value for p in TicketPriority]



@router.put("/tickets/{ticket_id}/status", response_model=TicketOut)
def update_ticket_status_by_assignee(
    project_id: int,
    ticket_id: int,
    payload: TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return ticket_repo.update_ticket_status_by_assignee(db, ticket_id, project_id, payload, current_user)

@router.put("/tickets/{ticket_id}/feedback", response_model=TicketOut)
def leave_feedback_by_creator(
    team_id: int,
    ticket_id: int,
    payload: TicketFeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return ticket_repo.leave_feedback_by_creator(db, ticket_id, team_id, payload, current_user)


@router.put("/tickets/{ticket_id}/assignee", response_model=TicketOut)
def update_ticket_assignee(
    team_id: int = Path(..., ge=1),
    ticket_id: int = Path(..., ge=1),
    payload: TicketAssigneeUpdate = Body(...),  # содержит только `assigned_to`
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_membership(current_user, team_id)
    return ticket_repo.update_ticket_assignee(db, ticket_id, payload, team_id)


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    team_id: int,
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_membership(current_user, team_id)
    ticket_repo.delete_ticket(db, ticket_id, team_id, current_user)
    return
