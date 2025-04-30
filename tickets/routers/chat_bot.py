import uuid
import re
from fastapi import Depends, APIRouter, Header, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from tickets.schemas.chat import ChatRequest, ChatResponse
from tickets import models
from tickets.repository.ai_service import analyze_tasks
from tickets.oaut2 import get_current_user
from tickets.repository import ai_memory, ai_service, ticket as ticket_repository
from tickets.schemas import ticket as ticket_schema
from tickets.repository.user import get_least_loaded_admins


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)
TASK_PREFIX = "help with creating ticket"
NO_ASSIGN_KEYWORDS = ["noone", "no one", "nobody", "leave it blank", "unassigned"]


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
        lower_body = body.lower()
        #videlyaem title and description from our analyze_tasks
        result = analyze_tasks(db, session_id, body, current_user.id)
        title = result.get("title", body[:50].strip())
        description = result.get("description", body).strip()
        #checking if we can find that we need to assign to somebody
        m = re.search(r"assign to\s+([A-Za-z0-9_]+)", lower_body)
        if m:
            assignee_name = m.group(1)
            #and if not, then check if user want to assign for noone
        elif any(kw in lower_body for kw in NO_ASSIGN_KEYWORDS):
            assignee_name = None
            #finally if didnt say then get least zagruzhenyy
        else:
            admins = get_least_loaded_admins(db, limit=2)
            assignee_name = admins[0].name if admins else None

        try:
            ticket_in = ticket_schema.TicketCreate(
                title=title,
                description=description,
                assigned_to_name=assignee_name
            )
            new_ticket = ticket_repository.create_ticket(
                db, ticket_in, current_user.id
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        # chat reply
        reply = f"🎫 Ticket #{new_ticket.id} created: {new_ticket.title}"
        if assignee_name:
            reply += f" (assigned to {assignee_name})"
        else:
            reply += " (currently unassigned)"

        return ChatResponse(
            reply=reply,
            session_id=session_id,
            ticket=new_ticket
        )

        # Fallback to normal AI chatbot behavior
    reply = ai_service.generate_reply(
        db, session_id, user_msg, user_id=current_user.id
    )
    return ChatResponse(reply=reply, session_id=session_id)