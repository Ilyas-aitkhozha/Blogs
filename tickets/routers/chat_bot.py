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
        print("[chat DEBUG] 🎯 matched create-ticket intent")
        _, body = user_msg.split(":", 1)
        parts = body.strip().split("\n", 1)
        title = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else title

        new_ticket = ticket_repository.create_ticket(
            db,
            ticket_schema.TicketCreate(title=title, description=description),
            current_user.id,
        )

        return ChatResponse(
            reply=f"✅ Ticket #{new_ticket.id} created: {new_ticket.title}",
            session_id=session_id,
            ticket=new_ticket
        )
    reply = ai_service.generate_reply(db, session_id, req.message, user_id = current_user.id)
    return ChatResponse(reply=reply, session_id=session_id)
