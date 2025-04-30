from sqlalchemy.orm import Session, joinedload
from tickets import models
from tickets.schemas.ticket import TicketCreate, TicketUpdate, TicketOut
from fastapi import HTTPException


def create_ticket(db: Session, ticket: TicketCreate, user_id: int):
    assigned_user_id = None
    if ticket.assigned_to_name:
        assigned_user = db.query(models.User).filter(models.User.name == ticket.assigned_to_name).first()
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found")
        if not assigned_user.is_available:
            raise HTTPException(status_code=400, detail="Assigned user not available")
        assigned_user_id = assigned_user.id

    new_ticket = models.Ticket(
        title=ticket.title,
        description=ticket.description,
        created_by=user_id,
        assigned_to=assigned_user_id
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    ticket_with_users = db.query(models.Ticket).options(
        joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee)
    ).filter(models.Ticket.id == new_ticket.id).first()

    return TicketOut.model_validate(ticket_with_users)

def get_ticket_by_id(db: Session, ticket_id: int):
    ticket = db.query(models.Ticket).options(
        joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee)
    ).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return TicketOut.model_validate(ticket)

def get_all_tickets(db: Session):
    tickets = db.query(models.Ticket).options(
        joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee)
    ).all()
    return [TicketOut.model_validate(t) for t in tickets]

def get_user_tickets(db: Session, user_id: int):
    tickets = db.query(models.Ticket).options(
        joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee)
    ).filter(models.Ticket.created_by == user_id).all()
    return [TicketOut.model_validate(t) for t in tickets]

def get_tickets_assigned_to_user(db: Session, current_user: models.User):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view assigned tickets.")
    tickets = db.query(models.Ticket).options(
        joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee)
    ).filter(
        models.Ticket.assigned_to == current_user.id,
        models.Ticket.status.in_(["open", "in_progress"])
    ).all()
    return [TicketOut.model_validate(t) for t in tickets]

ALLOWED_STATUS_TRANSITIONS = {
    "open": ["in_progress"],
    "in_progress": ["closed"],
    "closed": []
}

def update_ticket(db: Session, ticket_id: int, ticket_update: TicketUpdate, current_user: models.User):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    if ticket_update.status is not None:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can update ticket status.")
        if ticket.assigned_to != current_user.id:
            raise HTTPException(status_code=403, detail="You can only update status of tickets assigned to you.")
        current_status = ticket.status.value if hasattr(ticket.status, "value") else ticket.status
        next_status = ticket_update.status.value if hasattr(ticket_update.status, "value") else ticket_update.status
        allowed_next_statuses = ALLOWED_STATUS_TRANSITIONS.get(current_status, [])
        if next_status not in allowed_next_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from {current_status} to {next_status}. Allowed: {allowed_next_statuses}"
            )
        ticket.status = ticket_update.status
    if ticket_update.assigned_to is not None:
        if current_user.role != "user":
            raise HTTPException(status_code=403, detail="Only users can assign tickets.")
        if ticket.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="You can only reassign tickets you created.")
        new_assigned_user = db.query(models.User).filter(models.User.id == ticket_update.assigned_to).first()
        if not new_assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found.")
        if not new_assigned_user.is_available:
            raise HTTPException(status_code=400, detail="Assigned user is not available for tasks.")
        ticket.assigned_to = ticket_update.assigned_to
    db.commit()
    ticket_with_users = db.query(models.Ticket).options(
        joinedload(models.Ticket.creator),
        joinedload(models.Ticket.assignee)
    ).filter(models.Ticket.id == ticket.id).first()

    return TicketOut.model_validate(ticket_with_users)

def delete_ticket(db: Session, ticket_id: int):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    db.delete(ticket)
    db.commit()
    return {"detail": f"Ticket {ticket_id} deleted"}
