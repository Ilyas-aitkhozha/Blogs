import uuid
from fastapi import Depends, APIRouter, Header
from sqlalchemy.orm import Session
from ..database import get_db
from tickets.schemas.chat import ChatRequest, ChatResponse
from tickets import models
from tickets.oaut2 import get_current_user
from tickets.repository import ai_memory, ai_service, ticket as ticket_repository
from tickets.schemas import ticket as ticket_schema


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.post("/", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    session_id: str = Header(None),
    current_user: models.User = Depends(get_current_user)
):
    if session_id is None:
        session_id = str(uuid.uuid4())
        ai_memory.create_session(db, session_id, user_id=current_user.id)
    user_msg = req.message.strip()
    if user_msg.lower().startswith("create ticket:"):
        _, body = user_msg.split(":", 1)
        lines = [l.strip() for l in body.strip().split("\n") if l.strip()]

        title = lines[0]
        description_parts = []
        assignee_name = None

        for line in lines[1:]:
            low = line.lower()
            if low.startswith("assign to:"):
                assignee_name = line.split(":", 1)[1].strip()
            else:
                description_parts.append(line)
        description = "\n".join(description_parts) if description_parts else title

        ticket_in = ticket_schema.TicketCreate(
            title=title,
            description=description,
            assigned_to_name=assignee_name
        )
        new_ticket = ticket_repository.create_ticket(db, ticket_in, current_user.id)
        reply = f"Ticket #{new_ticket.id} created: {new_ticket.title}"
        if assignee_name:
            reply += f" (assigned to {assignee_name})"
        else:
            reply += " (currently unassigned)"

        return ChatResponse(
            reply=reply,
            session_id=session_id,
            ticket=new_ticket
        )

    reply = ai_service.generate_reply(db, session_id, user_msg, user_id=current_user.id)
    return ChatResponse(reply=reply, session_id=session_id)