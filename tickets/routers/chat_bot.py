import uuid
from fastapi import Depends, APIRouter, Header
from sqlalchemy.orm import Session
from ..database import get_db
from tickets.schemas.chat import ChatRequest, ChatResponse
from tickets import models
from tickets.repository.ai_service import analyze_tasks
from tickets.oaut2 import get_current_user
from tickets.repository import ai_memory, ai_service, ticket as ticket_repository
from tickets.schemas import ticket as ticket_schema
from tickets.repository.user import get_least_loaded_admin


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)
TASK_PREFIX = "help with creating ticket"

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
    if user_msg.lower().startswith(TASK_PREFIX):
        body = user_msg[len(TASK_PREFIX):].strip()
        result = analyze_tasks(db, session_id, body, current_user.id)
        title = result.get("title", body[:50])
        description = result.get("description", body)
        candidates = result.get("candidate_roles", [])
        assignee_name = candidates[0] if candidates else None
        if not assignee_name:
            least = get_least_loaded_admin(db)
            assignee_name = least.name if least else None

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