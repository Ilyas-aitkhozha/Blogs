import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import GenerativeModel
from tickets.repository.ai_memory import get_history, save_message
from tickets.repository.user import get_available_users_by_role

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


TASK_ANALYSIS_PROMPT = """
You are a JSON‐only extractor.
When given a free‐form task description, output exactly one valid JSON object with three keys:

  • title: a concise one‐line summary  
  • description: a brief paragraph explaining why and what needs doing  
  • candidate_roles: an array of usernames or roles best suited, ordered by least current workload  

Do NOT output markdown, code fences, bullet points, apologies, or any extra keys.  
Emit *only* the raw JSON object.
"""


def analyze_tasks(db, session_id: str, user_input: str, user_id: int):
    history = get_history(db, session_id, user_id)
    messages = [
        {"role": "user",   "parts": [TASK_ANALYSIS_PROMPT]}
    ]
    for msg in history:
        role = "assistant" if msg.role == "assistant" else "user"
        messages.append({"role": role, "parts": [msg.content]})
    messages.append({"role": "user", "parts": [user_input]})
    model = GenerativeModel("gemini-1.5-flash")
    raw = model.generate_content(messages).text.strip()

    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw

    start = raw.find("{")
    end   = raw.rfind("}")
    json_str = raw[start:end+1] if (start != -1 and end > start) else raw

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON decode error: {e}\nRaw response:\n{raw!r}")




def generate_reply(
    db,
    session_id: str,
    user_input: str,
    user_id: int
) -> str:
    history = get_history(db, session_id, user_id)   # now includes user_id
    messages = [
        {"role": "user", "parts": ["""You are an intelligent assistant that helps users and admins navigate the internal ticketing and chat system of a web platform.
The site has the following key roles and routes:
Two user roles: 'user' and 'admin'
Users can:
Create tickets (with title, description, optional assignee)
Assign tickets only to available admins
Use the chatbot to get help and suggestions for who is available
Admins can:
View all tickets
Update status of tickets (open, in_progress, closed)
Assign tickets to any user or admin

Available routes:
POST /tickets — create a new ticket
GET /tickets — view all tickets (admin only)
PUT /tickets/{id} — update status or assignment
GET /users/available-admins — get currently available admins
GET /users/available-users — get currently available users
POST /chat — chatbot entry point

The chatbot's job is to:
Guide users/admins through the system
Suggest available people for ticket assignment
Help troubleshoot simple usage problems
Provide brief explanations of what actions users can take based on their role
Always keep answers short, clear, and friendly. If you recognize a request for help, suggest available admins using /users/available-admins if needed.
"""]}
    ]
    for msg in history:
        role = "assistant" if msg.role == "assistant" else "user"
        messages.append({"role": role, "parts": [msg.content]})
    messages.append({"role": "user", "parts": [user_input]})
    model = GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(messages)
    reply = response.text.strip()
    if any(kw in user_input.lower() for kw in ["help", "problem", "issue", "debug", "assign", "urgent"]):
        admins = get_available_users_by_role(db, "admin")
        if admins:
            names = ', '.join([admin.name for admin in admins])
            reply += f"\n\nAvailable admins now: {names}. You can assign the ticket to one of them."
        else:
            reply += "\n\nNo admins are currently available."
    save_message(db, session_id, role="user",      content=user_input)
    save_message(db, session_id, role="assistant", content=reply)
    return reply