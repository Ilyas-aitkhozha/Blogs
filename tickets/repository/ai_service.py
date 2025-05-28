# tickets/repository/ai_service.py
import os
import re
import json
import logging
from typing import Optional, List, Dict, Any

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
    """Вернуть первый {...} блок из ответа LLM (если она «болтает лишнее»)."""
    m = re.search(r"\{.*\}", text, flags=re.S)
    return m.group(0) if m else None


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
    msgs = _history_to_messages(db, session_id, user_input, user_id)

    system_prompt = TICKET_CREATING_PROMPT + "\n\n" + _JSON_SCHEMA
    msgs.insert(0, {"role": "system", "parts": [system_prompt]})

    model = GenerativeModel("gemini-1.5-flash")
    raw_resp = model.generate_content(msgs).text.strip()

    try:
        return json.loads(raw_resp)
    except json.JSONDecodeError:
        raw_json = _extract_json(raw_resp)
        if raw_json:
            try:
                return json.loads(raw_json)
            except json.JSONDecodeError:
                pass

        logger.warning(
            "Gemini JSON parse fail. Raw (trunc): %r", raw_resp[:300]
        )
        return {
            "title": user_input[:50].strip(),
            "description": user_input.strip(),
            "candidate_roles": [],
        }


def generate_reply(
    db: Session,
    session_id: str,
    user_input: str,
    user_id: int,
    team_id: Optional[int] = None,
    system_prompt: str = BASE_PROMT,
) -> str:
    msgs = _history_to_messages(db, session_id, user_input, user_id)
    msgs.insert(0, {"role": "system", "parts": [system_prompt]})

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
