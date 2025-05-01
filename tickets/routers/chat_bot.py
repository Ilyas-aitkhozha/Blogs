import re
import uuid
from fastapi import Depends, APIRouter, Header, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from tickets.schemas.chat import ChatRequest, ChatResponse
from tickets import models
from tickets.repository.ai_service import analyze_tasks
from tickets.repository.ai_memory import create_session
from tickets.oaut2 import get_current_user
from tickets.repository import ai_service, ticket as ticket_repository
from tickets.schemas import ticket as ticket_schema
from tickets.repository.user import get_least_loaded_admins


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


TASK_PREFIX = "help with creating ticket"

# 1) фразы, означающие “не назначать никого”
NO_ASSIGN_RE = re.compile(
    r"\b("
    r"no\s?one"
    r"|nobody"
    r"|none"
    r"|anyone"
    r"|no assignment"
    r"|leave it blank"
    r"|unassigned"
    r"|dont assign"
    r"|don't assign"
    r"|do not assign"
    r")\b",
    re.IGNORECASE
)

# 2) явное “assign to X”, но не “assign to no one/anyone”
ASSIGN_RE = re.compile(
    r"assign to\s+"
    r"(?!no\s?one|none|nobody|anyone)\s*"
    r"([A-Za-z0-9_ ]+)",
    re.IGNORECASE
)


@router.post("/", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    session_id: str = Header(None),
    current_user: models.User = Depends(get_current_user)
):
    # 0) Если нет session_id — создаём новую сессию
    if session_id is None:
        session_id = str(uuid.uuid4())
        create_session(db, session_id, current_user.id)

    user_msg = req.message.strip()

    # 1) Создание тикета
    if user_msg.lower().startswith(TASK_PREFIX):
        body = user_msg[len(TASK_PREFIX):].strip()
        lower_body = body.lower()

        # 1.1) Запускаем AI-анализ, чтобы получить title, description и candidate_roles
        result = analyze_tasks(db, session_id, body, current_user.id)
        title = result.get("title", body[:50].strip())
        description = result.get("description", body).strip()
        candidates = result.get("candidate_roles", [])

        # 1.2) Логика назначения
        if NO_ASSIGN_RE.search(lower_body):
            assignee_name = None
        else:
            m = ASSIGN_RE.search(lower_body)
            if m:
                assignee_name = m.group(1).strip()
            elif candidates:
                assignee_name = candidates[0]
            else:
                admins = get_least_loaded_admins(db, limit=2)
                assignee_name = admins[0].name if admins else None

        # 1.3) Создаём тикет в БД
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

        # 1.4) Формируем ответ
        reply = f"🎫 Ticket #{new_ticket.id} created: {new_ticket.title}"
        reply += f" (assigned to {assignee_name})" if assignee_name else " (currently unassigned)"

        return ChatResponse(
            reply=reply,
            session_id=session_id,
            ticket=new_ticket
        )

    # 2) fallback — обычное поведение чат-бота
    reply = ai_service.generate_reply(
        db, session_id, user_msg, current_user.id
    )
    return ChatResponse(reply=reply, session_id=session_id)
