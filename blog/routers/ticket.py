from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from blog.schemas import ticket as ticket_schema
from blog.database import get_db
from blog.repository import ticket as ticket_repository
from blog.oaut2 import get_current_user
from blog import models

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

@router.post("/", response_model=ticket_schema.TicketOut)
def create_ticket(
    request: ticket_schema.TicketCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "user":
        raise HTTPException(status_code=403, detail="Only ordinary users can create tickets.")
    return ticket_repository.create_ticket(db, request, current_user.id)

@router.get("/", response_model=list[ticket_schema.TicketOut])
def get_all_tickets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view all tickets.")
    return ticket_repository.get_all_tickets(db)

@router.get("/{ticket_id}", response_model=ticket_schema.TicketOut)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
):
    ticket = ticket_repository.get_ticket_by_id(db, ticket_id)
    return ticket

@router.get("/my-created/", response_model=list[ticket_schema.TicketOut])
def get_my_created_tickets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return ticket_repository.get_user_tickets(db, current_user.id)

@router.get("/my-assigned/", response_model=list[ticket_schema.TicketOut])
def get_my_assigned_tickets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return ticket_repository.get_tickets_assigned_to_user(db, current_user)



@router.put("/{ticket_id}", response_model=ticket_schema.TicketOut)
def update_ticket(
    ticket_id: int,
    request: ticket_schema.TicketUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return ticket_repository.update_ticket(db, ticket_id, request, current_user)


@router.delete("/{ticket_id}", response_model = ticket_schema.TicketOut)
def delete_ticket(db: Session, ticket_id: int, current_user: models.User):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    if ticket.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="You are not allowed to delete this ticket.")
    db.delete(ticket)
    db.commit()
    return {"detail": f"Ticket {ticket_id} deleted"}

