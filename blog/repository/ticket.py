from sqlalchemy.orm import Session
from blog import models
from blog.schemas.ticket import TicketCreate, TicketUpdate
from fastapi import HTTPException

def create_ticket(db: Session, ticket: TicketCreate, user_id: int):
    assigned_user_id = None
    if ticket.assigned_to_name:
        assigned_user = db.query(models.User).filter(models.User.name == ticket.assigned_to_name).first()
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found")
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
    return new_ticket

def get_ticket_by_id(db: Session, ticket_id: int):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket

def get_all_tickets(db: Session):
    return db.query(models.Ticket).all()

def get_user_tickets(db: Session, user_id: int):
    return db.query(models.Ticket).filter(models.Ticket.created_by == user_id).all()

def get_tickets_assigned_to_user(db: Session, current_user: models.User):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view assigned tickets.")
    return db.query(models.Ticket).filter(
        models.Ticket.assigned_to == current_user.id,
        models.Ticket.status.in_(["open", "in_progress"])
    ).all()

def update_ticket(db: Session, ticket_id: int, ticket_update: TicketUpdate, current_user: models.User):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    if ticket_update.status is not None:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can change ticket status.")
        if ticket.assigned_to != current_user.id:
            raise HTTPException(status_code=403, detail="You can only change tickets assigned to you.")
        ticket.status = ticket_update.status
    if ticket_update.assigned_to is not None:
        if current_user.role != "user":
            raise HTTPException(status_code=403, detail="Only users can assign tickets.")
        ticket.assigned_to = ticket_update.assigned_to
    db.commit()
    db.refresh(ticket)
    return ticket

def delete_ticket(db: Session, ticket_id: int):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    db.delete(ticket)
    db.commit()
    return {"detail": f"Ticket {ticket_id} deleted"}
