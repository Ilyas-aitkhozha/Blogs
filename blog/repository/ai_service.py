import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import GenerativeModel
from blog.repository.ai_memory import get_history, save_message

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def generate_reply(db, session_id, user_input):
    # 1. Сохраняем сообщение пользователя
    save_message(db, session_id, role="user", content=user_input)

    # 2. Получаем историю из БД
    history = list(reversed(get_history(db, session_id)))

    # 3. Формируем список сообщений в формате Gemini
    messages = [{"role": "user", "parts": ["You are a helpful assistant."]}]
    for msg in history:
        messages.append({
            "role": msg.role if msg.role in ["user", "model", "assistant"] else "user",
            "parts": [msg.content]
        })
    messages.append({"role": "user", "parts": [user_input]})

    # 4. Создаём Gemini-модель
    model = GenerativeModel("gemini-1.5-flash")  # или "gemini-pro"

    # 5. Отправляем запрос
    response = model.generate_content(messages)
    reply = response.text.strip()

    # 6. Сохраняем ответ ассистента
    save_message(db, session_id, role="assistant", content=reply)

    return reply
