import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import GenerativeModel
from blog.repository.ai_memory import get_history, save_message

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def generate_reply(db, session_id, user_input):
    save_message(db, session_id, role="user", content=user_input)
    history = list(reversed(get_history(db, session_id)))
    messages = [{"role": "user", "parts": ["You are a helpful in the website about blogs assistant."]}]
    for msg in history:
        messages.append({
            "role": msg.role if msg.role in ["user", "model", "assistant"] else "user",
            "parts": [msg.content]
        })

    model = GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(messages)
    reply = response.text.strip()
    save_message(db, session_id, role="assistant", content=reply)
    return reply

