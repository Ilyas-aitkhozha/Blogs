import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import GenerativeModel
from blog.repository.ai_memory import get_history, save_message

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def generate_reply(db, session_id, user_input):
    #1: im loading history first
    history = list(reversed(get_history(db, session_id)))  #from oldest to newest convo (gemini need its in this order)

    #2: messages, and system prompt
    messages = [{"role": "user", "parts": ["You are a helpful assistant in the website about blogs."]}]
    for msg in history:
        messages.append({
            "role": msg.role if msg.role in ["user", "assistant", "model"] else "user",
            "parts": [msg.content]
        })

    #3: appending users message
    messages.append({"role": "user", "parts": [user_input]})

    model = GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(messages)
    reply = response.text.strip()

    #4: saev messages AFTER getting model reply
    save_message(db, session_id, role="user", content=user_input)
    save_message(db, session_id, role="assistant", content=reply)

    return reply


