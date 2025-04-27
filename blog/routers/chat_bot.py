import uuid
from fastapi import Depends, APIRouter, Header, HTTPException
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
    session_id: str = Header(None)
):
    if session_id is None:
        session_id = str(uuid.uuid4())
        create_session(db, session_id)
    else:
        if not get_session(db, session_id):
            raise HTTPException(status_code=400, detail="Session ID not found")
    reply = generate_reply(db, session_id, req.message)
    return ChatResponse(reply=reply)
