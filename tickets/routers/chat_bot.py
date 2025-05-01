import re
import uuid
from fastapi import Depends, APIRouter, Header, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from tickets.schemas.chat import ChatRequest, ChatResponse
from tickets import models
from tickets.repository.ai_service import analyze_tasks, report_with_metrics, generate_reply
from tickets.repository.ai_memory import create_session, save_message
from tickets.oaut2 import get_current_user
from tickets.repository import ticket as ticket_repository
from tickets.schemas import ticket as ticket_schema
from tickets.repository.user import  get_least_loaded_admins

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
    team_id = current_user.teams[0].id  # используем первую команду пользователя

    # 1) Создание тикета
    if user_msg.lower().startswith(TASK_PREFIX):
        body = user_msg[len(TASK_PREFIX):].strip()
        lower_body = body.lower()

        # 1.1) Запускаем AI-анализ задач для генерации заголовка и описания
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
                admins = get_least_loaded_admins(db=db,team_id=team_id,limit=2)
                assignee_name = admins[0].name if admins else None

        # 1.3) Создаём тикет в БД
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
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        # 1.4) Формируем ответ
        reply = f"🎫 Ticket #{new_ticket.id} created: {new_ticket.title}"
        reply += f" (assigned to {assignee_name})" if assignee_name else " (currently unassigned)"

        # Сохраняем и отсылаем сообщение
        save_message(db, session_id, role="user", content=user_msg)
        save_message(db, session_id, role="assistant", content=reply)
        return ChatResponse(reply=reply, session_id=session_id, ticket=new_ticket)

    # 2) Запрос отчёта по команде
    if user_msg.lower().startswith("/report"):
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

    # 3) Запрос диаграммы
    if any(k in user_msg.lower() for k in ["chart", "diagram", "visual"]):
        # Отправляем токен генерации диаграммы
        reply = f"GENERATE_CHART:STATUS_PIE:{team_id}"
        save_message(db, session_id, role="user", content=user_msg)
        save_message(db, session_id, role="assistant", content=reply)
        return ChatResponse(reply=reply, session_id=session_id)

    # 4) Fallback — обычное поведение чат-бота
    reply = generate_reply(
        db=db,
        session_id=session_id,
        user_input=user_msg,
        user_id=current_user.id,
        team_id=team_id
    )
    return ChatResponse(reply=reply, session_id=session_id)
