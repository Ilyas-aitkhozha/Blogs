from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, status, Body
from sqlalchemy.orm import Session
from tickets.database import get_db
from tickets.oaut2 import get_current_user
from tickets.schemas.ticket import TicketCreate, TicketUpdate, TicketOut
from tickets.repository import ticket as ticket_repo
from tickets import models

router = APIRouter(
    prefix="/teams/{team_id}",
    tags=["Team Tickets"],
)


def _ensure_membership(user: models.User, team_id: int) -> None:
    if not any(t.id == team_id for t in user.teams):
        raise HTTPException(status_code=403, detail="Нет доступа к этой команде.")


@router.post("/tickets", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    team_id: int = Path(..., ge=1),
    payload: TicketCreate = Depends(),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != "user":
        raise HTTPException(status_code=403, detail="Only ordinary users can create tickets.")
    _ensure_membership(current_user, team_id)
    return ticket_repo.create_ticket(db, payload, current_user.id, team_id)


@router.get("/tickets", response_model=List[TicketOut])
def list_tickets(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view all tickets.")
    _ensure_membership(current_user, team_id)
    return ticket_repo.get_all_tickets(db, team_id)


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(
    team_id: int,
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_membership(current_user, team_id)
    return ticket_repo.get_ticket_by_id(db, ticket_id, team_id)


@router.get("/tickets/my-created", response_model=List[TicketOut])
def my_created(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_membership(current_user, team_id)
    return ticket_repo.get_user_tickets(db, current_user.id, team_id)


@router.get("/tickets/my-assigned", response_model=List[TicketOut])
def my_assigned(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_membership(current_user, team_id)
    return ticket_repo.get_tickets_assigned_to_user(db, current_user, team_id)


@router.put("/tickets/{ticket_id}/status", response_model=TicketOut)
def update_ticket_status(
    ticket_id: int = Path(..., ge=1),
    team_id: int = Path(..., ge=1),
    payload: TicketUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_membership(current_user, team_id)
    return ticket_repo.update_ticket_status(db, ticket_id, payload, team_id)


@router.put("/tickets/{ticket_id}/assignee", response_model=TicketOut)
def update_ticket_assignee(
    team_id: int = Path(..., ge=1),
    ticket_id: int = Path(..., ge=1),
    payload: TicketUpdate = Body(...),  # содержит только `assigned_to`
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
