# in blog/routers/chat.py
from fastapi import APIRouter
from ..schemas import ChatRequest, ChatResponse
from ..repository.ai_service import generate_reply

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.post("/", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply = generate_reply(req.message)
    return ChatResponse(reply=reply)
