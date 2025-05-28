# tickets/repository/ai_service.py
import os
import re
import json
import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import GenerativeModel
from sqlalchemy.orm import Session

from tickets.repository.ai_memory import get_history, save_message
from tickets.repository.user import get_available_users_by_role
from tickets.repository.prompts import (
    METRIC_ANALYZE_PROMPT,
    TICKET_CREATING_PROMPT,
    BASE_PROMT,
)

from tickets.routers.analytics import compute_team_metrics

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

logger = logging.getLogger(__name__)
_TEAM_RE    = re.compile(r"\bteam\s*[-:]\s*([A-Za-z0-9_-]+)", re.I)
_PROJECT_RE = re.compile(r"\bproject\s*[-:]\s*([A-Za-z0-9 _-]+)", re.I)
_JSON_RE    = re.compile(r"\{.*\}", re.S)
_JSON_SCHEMA = """
Тебе присылают произвольный текст задачи.
Верни ТОЛЬКО JSON строго по образцу и ничего больше:

{
  "title": "<короткий заголовок>",
  "description": "<расширенное описание>",
  "candidate_roles": ["<имя1>", "<имя2>"]
}
"""

def _extract_json(text: str) -> str | None:
    m = _JSON_RE.search(text)
    return m.group(0) if m else None
def _regex_parse(text: str) -> Dict[str, str] | None:
    """
    Пытаемся выцепить team_code и project_name регэкспами.
    Возвращаем словарь или None, если чего-то нет.
    """
    team_m    = _TEAM_RE.search(text)
    project_m = _PROJECT_RE.search(text)
    if not (team_m and project_m):
        return None

    team_code    = team_m.group(1).strip()
    project_name = project_m.group(1).strip()

    # удаляем найденные куски из описания
    cleaned = _TEAM_RE.sub("", text)
    cleaned = _PROJECT_RE.sub("", cleaned).strip()

    # title = первые 50 символов без перевода строк
    title = cleaned.splitlines()[0][:50].strip()
    return {
        "title": title or "no title",
        "description": cleaned,
        "team_code": team_code,
        "project_name": project_name,
        "candidate_roles": [],
    }

def _history_to_messages(
    db: Session,
    session_id: str,
    user_input: str,
    user_id: int
) -> List[Dict[str, Any]]:
    history = get_history(db, session_id, user_id)
    msgs: List[Dict[str, Any]] = []

    for msg in history:
        role = "assistant" if msg.role == "assistant" else "user"
        msgs.append({"role": role, "parts": [msg.content]})

    msgs.append({"role": "user", "parts": [user_input]})
    return msgs


def analyze_tasks(
    db: Session,
    session_id: str,
    user_input: str,
    user_id: int,
) -> Dict[str, Any]:

    # 0) пробуем быстрый regex-парс
    parsed = _regex_parse(user_input)
    if parsed:
        return parsed                     # ← успех, LLM не вызываем

    # 1) собираем историю
    msgs = _history_to_messages(db, session_id, user_input, user_id)

    # 2) system-prompt (роль "user" для Gemini Flash)
    system_prompt = TICKET_CREATING_PROMPT + "\n\n" + _JSON_SCHEMA
    msgs.insert(0, {"role": "user", "parts": [system_prompt]})

    # 3) вызываем модель
    model = GenerativeModel("gemini-1.5-flash")
    raw = model.generate_content(msgs).text.strip()

    # 4) парсим JSON
    try:
        data: Dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        raw_json = _extract_json(raw)
        if raw_json:
            try:
                data = json.loads(raw_json)
            except json.JSONDecodeError:
                data = None
        else:
            data = None

    if not data or not isinstance(data, dict):
        logger.warning("Gemini JSON parse fail. Raw(300): %r", raw[:300])
        raise HTTPException(
            422,
            "Could not extract JSON. "
            "Make sure to include `team - <code>` and `project - <name>`."
        )

    # проверяем обязательные поля
    for key in ("team_code", "project_name"):
        if not data.get(key):
            raise HTTPException(
                422,
                f"Missing required field: {key}. "
                "Add lines `team - …`, `project - …`."
            )

    return data


def generate_reply(
    db: Session,
    session_id: str,
    user_input: str,
    user_id: int,
    team_id: Optional[int] = None,
    system_prompt: str = BASE_PROMT,
) -> str:
    msgs = _history_to_messages(db, session_id, user_input, user_id)
    msgs.insert(0, {"role": "user", "parts": [system_prompt]})

    model = GenerativeModel("gemini-1.5-flash")
    reply = model.generate_content(msgs).text.strip()
    if any(
        kw in user_input.lower()
        for kw in ["help", "problem", "issue", "debug", "assign", "urgent"]
    ):
        admins = get_available_users_by_role(db, "admin", team_id)
        if admins:
            names = ", ".join(admin.name for admin in admins)
            reply += (
                f"\n\nAvailable admins right now: {names}. "
                "You can assign the ticket to one of them."
            )
        else:
            reply += "\n\nNo admins are currently available."

    save_message(db, session_id, role="user", content=user_input)
    save_message(db, session_id, role="assistant", content=reply)
    return reply

def report_with_metrics(
    db: Session,
    session_id: str,
    user_input: str,
    user_id: int,
    team_id: int,
) -> str:
    metrics = compute_team_metrics(team_id, db)
    system_prompt = METRIC_ANALYZE_PROMPT.replace(
        "{{METRICS_JSON}}", json.dumps(metrics, ensure_ascii=False)
    )

    return generate_reply(
        db=db,
        session_id=session_id,
        user_input=user_input,
        user_id=user_id,
        team_id=team_id,
        system_prompt=system_prompt,
    )
