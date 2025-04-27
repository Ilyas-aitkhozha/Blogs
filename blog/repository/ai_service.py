import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import GenerativeModel
from blog.repository.ai_memory import get_history, save_message

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def generate_reply(
    db,
    session_id: str,
    user_input: str,
    user_id: int
) -> str:
    history = get_history(db, session_id, user_id)   # now includes user_id
    messages = [
        {"role": "user", "parts": ["You are a helpful assistant on our blogging site."]}
    ]
    for msg in history:
        role = "assistant" if msg.role == "assistant" else "user"
        messages.append({"role": role, "parts": [msg.content]})
    messages.append({"role": "user", "parts": [user_input]})
    model = GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(messages)
    reply = response.text.strip()
    save_message(db, session_id, role="user",      content=user_input)
    save_message(db, session_id, role="assistant", content=reply)
    return reply