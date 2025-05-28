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

    # пытаемся взять первую команду, если есть
    current_team = current_user.teams[0] if current_user.teams else None
    current_project = current_user.project_users[0] if current_user.project_users else None

    # флаги команд, которые требуют участия в команде
    is_ticket_cmd = user_msg.lower().startswith(TASK_PREFIX)
    is_report_cmd = user_msg.lower().startswith("/report")
    is_chart_cmd = any(k in user_msg.lower() for k in ["chart", "diagram", "visual"])

    # если команда-операция и нет membership → совет вступить
    if is_ticket_cmd:
        logger.info("ai bot creating ticket")
        body = user_msg[len(TASK_PREFIX):].strip()

        # 1) вытягиваем JSON {title, description, team_code, project_name …}
        try:
            parsed = analyze_tasks(db, session_id, body, current_user.id)
        except HTTPException as exc:
            save_message(db, session_id, role="assistant", content=exc.detail)
            return ChatResponse(reply=exc.detail, session_id=session_id)

        team_code = parsed["team_code"].strip()
        project_name = parsed["project_name"].strip()
        title = parsed["title"]
        description = parsed["description"]
        candidates = parsed.get("candidate_roles", [])

        # 2) ищем команду
        team = db.query(models.Team).filter_by(code=team_code).first()
        if not team:
            reply = f"⚠ Команда с кодом «{team_code}» не найдена."
            save_message(db, session_id, role="assistant", content=reply)
            return ChatResponse(reply=reply, session_id=session_id)

        # проверяем, что пользователь состоит в этой команде
        if team.id not in [t.id for t in current_user.teams]:
            reply = "⚠ Вы не состоите в указанной команде и не можете создавать там тикеты."
            save_message(db, session_id, role="assistant", content=reply)
            return ChatResponse(reply=reply, session_id=session_id)

        # 3) ищем проект
        project = (
            db.query(models.Project)
            .filter(models.Project.name.ilike(project_name))
            .first()
        )
        if not project:
            reply = f"⚠ Проект «{project_name}» не найден."
            save_message(db, session_id, role="assistant", content=reply)
            return ChatResponse(reply=reply, session_id=session_id)

        # 4) определяем потенциального исполнителя (по имени в тексте / авто-выбор)
        if NO_ASSIGN_RE.search(body.lower()):
            assignee_name = None
        else:
            m = ASSIGN_RE.search(body.lower())
            if m:
                assignee_name = m.group(1).strip()
            elif candidates:
                assignee_name = candidates[0]
            else:
                admins = get_least_loaded_admins(db, team_id=team.id, limit=1)
                assignee_name = admins[0].name if admins else None

        # 5) собираем TicketCreate
        ticket_in = ticket_schema.TicketCreate(
            title=title,
            description=description,
            assigned_to_name=assignee_name,
            team_id=team.id,
            project_id=project.id,
        )

        # 6) создаём тикет
        new_ticket = ticket_repository.create_ticket(
            db=db,
            ticket_in=ticket_in,
            user_id=current_user.id,
            project_id=project.id,
            team_id=team.id,
        )

        reply = (
                f"🎫 Тикет #{new_ticket.id} создан (команда {team.code}, проект {project.name}) — "
                f"«{new_ticket.title}»"
                + (f", исполнитель: {assignee_name}" if assignee_name else ", без исполнителя")
        )
        save_message(db, session_id, role="assistant", content=reply)
        return ChatResponse(reply=reply, session_id=session_id, ticket=new_ticket)

        # ── 1. /report ─────────────────────────────────────────────────────────
    if is_report_cmd:
        reply = report_with_metrics(
            db=db,
            session_id=session_id,
            user_input=user_msg,
            user_id=current_user.id,
            team_id=current_user.teams[0].id if current_user.teams else None,
        )
        save_message(db, session_id, role="assistant", content=reply)
        return ChatResponse(reply=reply, session_id=session_id)

        # ── 2. /chart ──────────────────────────────────────────────────────────
    if is_chart_cmd and current_user.teams:
        team_id = current_user.teams[0].id
        reply = f"GENERATE_CHART:STATUS_PIE:{team_id}"
        save_message(db, session_id, role="assistant", content=reply)
        return ChatResponse(reply=reply, session_id=session_id)

        # ── 3. обычный ответ LLM ───────────────────────────────────────────────
    reply = generate_reply(
        db=db,
        session_id=session_id,
        user_input=user_msg,
        user_id=current_user.id
    )
    save_message(db, session_id, role="assistant", content=reply)
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
