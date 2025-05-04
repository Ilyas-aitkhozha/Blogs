import os
import json
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from sqlalchemy.orm import Session
from google.generativeai import GenerativeModel
from tickets.repository.ai_memory import get_history, save_message
from tickets.repository.user import get_available_users_by_role
from tickets.repository.prompts import METRIC_ANALYZE_PROMPT, TICKET_CREATING_PROMPT,BASE_PROMT
from tickets.routers.analytics import compute_team_metrics
logger = logging.getLogger(__name__)
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

#helper
def messages(db, session_id: str, user_input: str, user_id: int) -> list[dict]:
    history = get_history(db, session_id, user_id)
    messages = []
    for msg in history:
        role = "assistant" if msg.role == "assistant" else "user"
        messages.append({"role": role, "parts": [msg.content]})
    messages.append({"role": "user", "parts": [user_input]})
    return messages


def analyze_tasks(db, session_id: str, user_input: str, user_id: int):
    messages_list = messages(db, session_id, user_input, user_id)
    messages_list.insert(0, {"role": "user", "parts": [TICKET_CREATING_PROMPT]})  # system prompt
    model = GenerativeModel("gemini-1.5-flash")
    raw = model.generate_content(messages_list).text.strip()

    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw

    start = raw.find("{")
    end   = raw.rfind("}")
    json_str = raw[start:end+1] if (start != -1 and end > start) else raw

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error("JSON decode error from Gemini: %s\nRaw: %r", e, raw)
        raise ValueError(f"JSON decode error: {e}\nRaw response:\n{raw!r}")




def generate_reply(
    db,
    session_id: str,
    user_input: str,
    user_id: int,
    team_id: int,
    system_prompt: str = BASE_PROMT  # <— новый параметр с дефолтом
) -> str:
    messages_list = messages(db, session_id, user_input, user_id)
    messages_list.insert(0, {"role": "user", "parts": [system_prompt]})  # вставляем системный промпт
    model = GenerativeModel("gemini-1.5-flash")
    reply = model.generate_content(messages_list).text.strip()

    if any(kw in user_input.lower() for kw in ["help", "problem", "issue", "debug", "assign", "urgent"]):
        admins = get_available_users_by_role(db, "admin",team_id)
        if admins:
            names = ', '.join([admin.name for admin in admins])
            reply += f"\n\nAvailable admins now: {names}. You can assign the ticket to one of them."
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
    team_id: int
) -> str:
    metrics = compute_team_metrics(team_id, db)
    system_prompt = METRIC_ANALYZE_PROMPT.replace(
        "{{METRICS_JSON}}",
        json.dumps(metrics, ensure_ascii=False)
    )
    return generate_reply(
        db=db,
        session_id=session_id,
        user_input=user_input,
        user_id=user_id,
        team_id=team_id,
        system_prompt=system_prompt
    )