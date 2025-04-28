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
    current_user: models.User = Depends(get_current_user)
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


ALLOWED_STATUS_TRANSITIONS = {
    "open": ["in_progress"],
    "in_progress": ["closed"],
    "closed": []
}

@router.put("/{ticket_id}", response_model=ticket_schema.TicketOut)
def update_ticket(
    ticket_id: int,
    request: ticket_schema.TicketUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    if request.status is not None:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can update ticket status.")
        if ticket.assigned_to != current_user.id:
            raise HTTPException(status_code=403, detail="You can only update status of tickets assigned to you.")
        current_status = ticket.status.value if hasattr(ticket.status, "value") else ticket.status
        next_status = request.status.value if hasattr(request.status, "value") else request.status
        allowed_next_statuses = ALLOWED_STATUS_TRANSITIONS.get(current_status, [])
        if next_status not in allowed_next_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from {current_status} to {next_status}. Allowed: {allowed_next_statuses}"
            )
        ticket.status = request.status
    if request.assigned_to is not None:
        if current_user.role != "user":
            raise HTTPException(status_code=403, detail="Only users can assign tickets.")
        if ticket.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="You can only reassign tickets you created.")
        ticket.assigned_to = request.assigned_to
    db.commit()
    db.refresh(ticket)
    return ticket




def delete_ticket(db: Session, ticket_id: int, current_user: models.User):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    if ticket.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="You are not allowed to delete this ticket.")
    db.delete(ticket)
    db.commit()
    return {"detail": f"Ticket {ticket_id} deleted"}

