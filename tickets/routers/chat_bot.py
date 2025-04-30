import uuid
from fastapi import Depends, APIRouter, Header
from sqlalchemy.orm import Session
from ..database import get_db
from tickets.schemas.chat import ChatRequest, ChatResponse
from tickets import models
from tickets.oaut2 import get_current_user
from tickets.repository import ai_memory, ai_service

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.post("/", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    session_id: str = Header(None),
    current_user: models.User = Depends(get_current_user)
):
    if session_id is None:
        session_id = str(uuid.uuid4())
        ai_memory.create_session(db, session_id, user_id=current_user.id)

    reply = ai_service.generate_reply(db, session_id, req.message, user_id = current_user.id)
    return ChatResponse(reply=reply, session_id=session_id)
