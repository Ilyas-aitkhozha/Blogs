from typing import List
from datetime import datetime,timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from tickets import models
from tickets.schemas.ticket import TicketCreate, TicketOut, TicketStatusUpdate, TicketAssigneeUpdate, TicketFeedbackUpdate

#--------------------------------------- CREATE
def create_ticket(
    db: Session,
    ticket_in: TicketCreate,
    user_id: int,
    team_id: int,
) -> TicketOut:
    assigned_user_id = None
    if ticket_in.assigned_to_name: #if user assigned, then checking if mate in the db
        assigned_user = (
            db.query(models.User)
            .filter(
                models.User.name == ticket_in.assigned_to_name,
                models.User.teams.any(models.Team.id == team_id)
            )
            .first()
        )
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found in this team")
        if not assigned_user.is_available:
            raise HTTPException(status_code=400, detail="Assigned user not available")
        assigned_user_id = assigned_user.id
#if all requirements passed, creating ticket
    new_ticket = models.Ticket(
        title=ticket_in.title,
        description=ticket_in.description,
        created_by=user_id,
        assigned_to=assigned_user_id,
        team_id=team_id,
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return _load_ticket_with_users(db, new_ticket.id)

#------------------------------GET LOGICS
def get_ticket_by_id(db: Session, ticket_id: int, team_id: int) -> TicketOut:
    #getting ticket by id in the team
    ticket = (
        db.query(models.Ticket)
        .options(joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee))
        .filter(models.Ticket.id == ticket_id, models.Ticket.team_id == team_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return TicketOut.model_validate(ticket)


def get_all_tickets(db: Session, team_id: int) -> List[TicketOut]:
    tickets = (
        db.query(models.Ticket)
        .options(joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee))
        .filter(models.Ticket.team_id == team_id)
        .all()
    )
    return [TicketOut.model_validate(t) for t in tickets]


def get_user_tickets(db: Session, user_id: int, team_id: int) -> List[TicketOut]:
    tickets = (
        db.query(models.Ticket)
        .options(joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee))
        .filter(models.Ticket.created_by == user_id, models.Ticket.team_id == team_id)
        .all()
    )
    return [TicketOut.model_validate(t) for t in tickets]


def get_tickets_assigned_to_user(
    db: Session,
    current_user: models.User,
    team_id: int,
) -> List[TicketOut]:
    if current_user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins can view assigned tickets.")

    tickets = (
        db.query(models.Ticket)#economim zaprosi by using options
        .options(joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee))
        .filter(
            models.Ticket.assigned_to == current_user.id,
            models.Ticket.team_id == team_id,
            models.Ticket.status.in_(["open", "in_progress"]),
        )
        .all()
    )
    return [TicketOut.model_validate(t) for t in tickets]


ALLOWED_STATUS_TRANSITIONS = {
    "open": ["in_progress"],
    "in_progress": ["closed"],
    "closed": [],
}

# ------------------------------------------UPDATE LOGIC
def update_ticket_status(db: Session, ticket_id: int, update: TicketStatusUpdate, team_id: int, current_user: models.User) -> TicketOut:
    ticket = db.query(models.Ticket).filter(
        models.Ticket.id == ticket_id,
        models.Ticket.team_id == team_id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    curr = ticket.status.value
    nxt = update.status.value
    if nxt not in ALLOWED_STATUS_TRANSITIONS[curr]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {curr} to {nxt}. Allowed: {ALLOWED_STATUS_TRANSITIONS[curr]}",
        )

    if update.feedback is not None or update.confirmed is not None:
        if ticket.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Only creator can leave feeadback or confirm.")
    ticket.feedback = update.feedback
    ticket.confirmed = update.confirmed
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    return _load_ticket_with_users(db, ticket.id)


def update_ticket_feedback(db: Session, ticket: models.Ticket, payload: TicketFeedbackUpdate) -> models.Ticket:
    ticket.feedback = payload.feedback
    ticket.confirmed = payload.confirmed
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    return ticket

def update_ticket_assignee(db: Session, ticket_id: int, update: TicketAssigneeUpdate, team_id: int) -> TicketOut:
    ticket = db.query(models.Ticket).filter(
        models.Ticket.id == ticket_id,
        models.Ticket.team_id == team_id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    new_user = db.query(models.User).filter(
        models.User.id == update.assigned_to,
        models.User.teams.any(models.Team.id == team_id)
    ).first()

    if not new_user:
        raise HTTPException(status_code=404, detail="Assigned user not in this team")
    if not new_user.is_available:
        raise HTTPException(status_code=400, detail="Assigned user not available")

    ticket.assigned_to = update.assigned_to
    db.commit()
    return _load_ticket_with_users(db, ticket.id)


# --------------------------------DELETE TICKET
def delete_ticket(
    db: Session,
    ticket_id: int,
    team_id: int,
    current_user: models.User,
) -> None:
    ticket = (
        db.query(models.Ticket)
        .filter(models.Ticket.id == ticket_id, models.Ticket.team_id == team_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    if ticket.created_by != current_user.id and current_user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Not permitted to delete this ticket.")

    db.delete(ticket)
    db.commit()

#----------------------------------HELPERS
def _load_ticket_with_users(db: Session, ticket_id: int) -> TicketOut:
    ticket = (
        db.query(models.Ticket)
        .options(joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee))
        .filter(models.Ticket.id == ticket_id)
        .first()
    )
    return TicketOut.model_validate(ticket)