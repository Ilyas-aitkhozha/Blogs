from sqlalchemy.orm import Session
from blog import models
from blog.schemas.ticket import TicketCreate, TicketUpdate
from fastapi import HTTPException

def create_ticket(db: Session, ticket: TicketCreate, user_id: int):
    new_ticket = models.Ticket(
        title=ticket.title,
        description=ticket.description,
        created_by=user_id
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

def update_ticket(db: Session, ticket_id: int, ticket_update: TicketUpdate):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    if ticket_update.status is not None:
        ticket.status = ticket_update.status
    if ticket_update.assigned_to is not None:
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
