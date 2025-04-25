import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

_model = genai.GenerativeModel(model_name="gemini-1.5-flash")

def generate_reply(prompt: str) -> str:
    resp = _model.generate_content(prompt)
    return resp.text
