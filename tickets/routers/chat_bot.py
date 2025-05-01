import re
from fastapi import Depends, APIRouter, Header, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from tickets.schemas.chat import ChatRequest, ChatResponse
from tickets import models
from tickets.repository.ai_service import analyze_tasks
from tickets.oaut2 import get_current_user
from tickets.repository import  ai_service, ticket as ticket_repository
from tickets.schemas import ticket as ticket_schema
from tickets.repository.user import get_least_loaded_admins


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)
TASK_PREFIX = "help with creating ticket"

# 1) phrases that mean “no assignment”
NO_ASSIGN_RE = re.compile(
    r"\b(no\s?one|nobody|none|no assignment|leave it blank|unassigned)\b",
    re.IGNORECASE
)

# 2) explicit “assign to X”, but not “assign to no one”
ASSIGN_RE = re.compile(
    r"assign to\s+(?!no\s?one|none|nobody)\s*([A-Za-z0-9_ ]+)",
    re.IGNORECASE
)


@router.post("/", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    session_id: str = Header(None),
    current_user: models.User = Depends(get_current_user)
):
    # --- session setup omitted for brevity ---

    user_msg = req.message.strip()
    if user_msg.lower().startswith(TASK_PREFIX):
        body = user_msg[len(TASK_PREFIX):].strip()
        lower_body = body.lower()

        # 1) run your AI analysis to get title/description + candidate_roles
        result = analyze_tasks(db, session_id, body, current_user.id)
        title = result.get("title", body[:50].strip())
        description = result.get("description", body).strip()
        candidates = result.get("candidate_roles", [])

        # 2) detect “no assignment” first
        if NO_ASSIGN_RE.search(lower_body):
            assignee_name = None

        # 3) then explicit “assign to X”, excluding “no one”
        else:
            m = ASSIGN_RE.search(lower_body)
            if m:
                assignee_name = m.group(1).strip()
            # 4) else use AI‐suggested candidate
            elif candidates:
                assignee_name = candidates[0]
            # 5) final fallback: least‐loaded admins
            else:
                admins = get_least_loaded_admins(db, limit=2)
                assignee_name = admins[0].name if admins else None

        # 6) create the ticket
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

        # 7) build your reply
        reply = f"🎫 Ticket #{new_ticket.id} created: {new_ticket.title}"
        reply += f" (assigned to {assignee_name})" if assignee_name else " (currently unassigned)"

        return ChatResponse(reply=reply, session_id=session_id, ticket=new_ticket)

    # fallback to normal chat
    reply = ai_service.generate_reply(db, session_id, user_msg, user_id=current_user.id)
    return ChatResponse(reply=reply, session_id=session_id)