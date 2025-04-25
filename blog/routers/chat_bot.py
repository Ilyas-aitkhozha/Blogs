# in blog/routers/chat.py
from fastapi import Depends, APIRouter, Header
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import ChatRequest, ChatResponse
from ..repository.ai_service import generate_reply

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.post("/", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    session_id: str = Header(...)
):
    reply = generate_reply(db, session_id, req.message)
    return ChatResponse(reply=reply)
