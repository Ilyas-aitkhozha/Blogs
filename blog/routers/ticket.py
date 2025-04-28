from fastapi import APIRouter, Depends
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
def create_ticket(request: ticket_schema.TicketCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return ticket_repository.create_ticket(db, request, current_user.id)

@router.get("/{id}", response_model=ticket_schema.TicketOut)
def get_ticket(id: int, db: Session = Depends(get_db)):
    return ticket_repository.get_ticket_by_id(db, id)

@router.get("/", response_model=list[ticket_schema.TicketOut])
def get_all_tickets(db: Session = Depends(get_db)):
    return ticket_repository.get_all_tickets(db)

@router.get("/my/", response_model=list[ticket_schema.TicketOut])
def get_my_tickets(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return ticket_repository.get_user_tickets(db, current_user.id)

@router.put("/{id}", response_model=ticket_schema.TicketOut)
def update_ticket(id: int, request: ticket_schema.TicketUpdate, db: Session = Depends(get_db)):
    return ticket_repository.update_ticket(db, id, request)

@router.delete("/{id}")
def delete_ticket(id: int, db: Session = Depends(get_db)):
    return ticket_repository.delete_ticket(db, id)
