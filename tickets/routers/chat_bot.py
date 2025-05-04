import re
from fastapi import Depends, APIRouter, HTTPException, Path
from sqlalchemy.orm import Session
import logging
from ..database import get_db
from tickets.schemas.chat import ChatRequest, ChatResponse
from tickets import models
from tickets.repository.ai_service import analyze_tasks, report_with_metrics, generate_reply
from tickets.repository.ai_memory import get_or_create_session, save_message
from tickets.oauth2 import get_current_user
from tickets.repository import ticket as ticket_repository
from tickets.schemas import ticket as ticket_schema
from tickets.repository.user import get_least_loaded_admins
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

TASK_PREFIX = "help with creating ticket"

# phrases for situation where user dont assing
NO_ASSIGN_RE = re.compile(
    r"\b("
    r"no\s?one|nobody|none|anyone|no assignment|leave it blank|unassigned|dont assign|don't assign|do not assign"
    r")\b",
    re.IGNORECASE
)

# “assign to X”, but not “assign to no one/anyone”
ASSIGN_RE = re.compile(
    r"assign to\s+(?!no\s?one|none|nobody|anyone)\s*([A-Za-z0-9_ ]+)",
    re.IGNORECASE
)



@router.post("", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    session_record = get_or_create_session(db, current_user.id)
    session_id = session_record.id
    user_msg = req.message.strip()
    team_id = current_user.teams[0].id

    # creating ticket
    if user_msg.lower().startswith(TASK_PREFIX):
        logger.info("ai bot creating ticket")
        body = user_msg[len(TASK_PREFIX):].strip()
        lower_body = body.lower()
        result = analyze_tasks(db, session_id, body, current_user.id)
        title = result.get("title", body[:50].strip())
        description = result.get("description", body).strip()
        candidates = result.get("candidate_roles", [])

        if NO_ASSIGN_RE.search(lower_body):
            assignee_name = None
        else:
            m = ASSIGN_RE.search(lower_body)
            if m:
                assignee_name = m.group(1).strip()
            elif candidates:
                assignee_name = candidates[0]
            else:
                admins = get_least_loaded_admins(db=db, team_id=team_id, limit=2)
                assignee_name = admins[0].name if admins else None

        try:
            ticket_in = ticket_schema.TicketCreate(
                title=title,
                description=description,
                assigned_to_name=assignee_name
            )
            new_ticket = ticket_repository.create_ticket(
                db=db,
                ticket_in=ticket_in,
                user_id=current_user.id,
                team_id=team_id
            )
        except HTTPException:
            logger.warning(
                "HTTPException while creating ticket: %s  User: %s  Team: %s  Title: %r",
                HTTPException,
                current_user.id,
                team_id,
                title
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error while creating ticket  User: %s  Team: %s  Title: %r  Error: %s",
                current_user.id,
                team_id,
                title,
                str(e),
                exc_info=True  # vivodit stack trace
            )
            raise HTTPException(status_code=500, detail="Internal server error")

        reply = f"🎫 Ticket #{new_ticket.id} created: {new_ticket.title}"
        if assignee_name:
            reply += f" (assigned to {assignee_name})"
        else:
            reply += " (currently unassigned)"

        save_message(db, session_id, role="user", content=user_msg)
        save_message(db, session_id, role="assistant", content=reply)
        return ChatResponse(reply=reply, session_id=session_id, ticket=new_ticket)

    # text report
    if user_msg.lower().startswith("/report"):
        logger.info("ai bot reporting ticket")
        reply = report_with_metrics(
            db=db,
            session_id=session_id,
            user_input=user_msg,
            user_id=current_user.id,
            team_id=team_id
        )
        save_message(db, session_id, role="user", content=user_msg)
        save_message(db, session_id, role="assistant", content=reply)
        return ChatResponse(reply=reply, session_id=session_id)

    # graph
    if any(k in user_msg.lower() for k in ["chart", "diagram", "visual"]):
        logger.info("ai bot reporting ticket visuaalllyy")
        reply = f"GENERATE_CHART:STATUS_PIE:{team_id}"
        save_message(db, session_id, role="user", content=user_msg)
        save_message(db, session_id, role="assistant", content=reply)
        return ChatResponse(reply=reply, session_id=session_id)

    # basic chat
    reply = generate_reply(
        db=db,
        session_id=session_id,
        user_input=user_msg,
        user_id=current_user.id,
        team_id=team_id
    )
    return ChatResponse(reply=reply, session_id=session_id)

@router.post("/message", response_model=ChatResponse)
def open_chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    session_record = get_or_create_session(db, current_user.id)
    session_id = session_record.id
    user_msg = req.message.strip()
    team_id = current_user.teams[0].id

    reply = generate_reply(
        db=db,
        session_id=session_id,
        user_input=user_msg,
        user_id=current_user.id,
        team_id=team_id
    )
    save_message(db, session_id, role="user", content=user_msg)
    save_message(db, session_id, role="assistant", content=reply)
    return ChatResponse(reply=reply, session_id=session_id)

@router.get("/report", response_model=ChatResponse)
def get_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    session_record = get_or_create_session(db, current_user.id)
    session_id = session_record.id
    team_id = current_user.teams[0].id
    reply = report_with_metrics(
        db=db,
        session_id=session_id,
        user_input="/report",
        user_id=current_user.id,
        team_id=team_id
    )
    save_message(db, session_id, role="assistant", content=reply)
    return ChatResponse(reply=reply, session_id=session_id)

@router.get("/chart", response_model=ChatResponse)
def get_chart(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    session_record = get_or_create_session(db, current_user.id)
    session_id = session_record.id
    team_id = current_user.teams[0].id
    reply = f"GENERATE_CHART:STATUS_PIE:{team_id}"
    save_message(db, session_id, role="assistant", content=reply)
    return ChatResponse(reply=reply, session_id=session_id)

@router.post("/create-ticket", response_model=ChatResponse)
def post_create_ticket(
    ticket_in: ticket_schema.TicketCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    session_record = get_or_create_session(db, current_user.id)
    session_id = session_record.id
    try:
        new_ticket = ticket_repository.create_ticket(
            db=db,
            ticket_in=ticket_in,
            user_id=current_user.id,
            team_id=current_user.teams[0].id
        )
    except HTTPException:
        raise
    reply = f"🎫 Ticket #{new_ticket.id} created: {new_ticket.title}"
    save_message(db, session_id, role="assistant", content=reply)
    return ChatResponse(reply=reply, session_id=session_id, ticket=new_ticket)
