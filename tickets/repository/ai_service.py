import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import GenerativeModel
from tickets.repository.ai_memory import get_history, save_message
from tickets.repository.user import get_available_users_by_role

load_dotenv()
TASK_ANALYSIS_PROMPT ="""
You will receive a user’s free-form task description.
Respond ONLY with valid JSON containing:
  - title: a concise one-line summary of the task
  - description: a brief paragraph elaborating on why and what needs doing
  - candidate_roles: a JSON array of usernames or roles best suited, ordered by least current workload
Do NOT include any extra text outside that JSON and output strict JSON with closing bracket.
"""
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def analyze_tasks(db, session_id:str,user_input:str,user_id):
    history = get_history(db, session_id, user_id)
    messages = [
        {"role":"user", "parts": [TASK_ANALYSIS_PROMPT] }
    ]
    for msg in history:
        role = "assistant" if msg.role == "assistant" else "user"
        messages.append({"role": role, "parts": [msg.content]})
    messages.append({"role": "user", "parts": [user_input]})
    model = GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(messages).text
    start = response.find("{")
    end = response.rfind("}")
    if start != -1 and end != -1 and end > start:
        json_str = response[start: end + 1]
    else:
        json_str = response
    try:
        return json.loads(json_str)
    except json.decoder.JSONDecodeError:
        raise ValueError("Could not decode response")


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