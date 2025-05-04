from sqlalchemy.orm import Session
from tickets.models import SessionRecord, ChatMessage
#creating session for detailed info about chat_messages
def create_session(db: Session, session_id: str, user_id: int):
    new = SessionRecord(id=session_id, user_id=user_id)
    db.add(new); db.commit(); db.refresh(new)
    return new


def get_session(db: Session, session_id: str):
    return db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
#we are getting history of dialogue, context window in another words
def get_history(db: Session, session_id: str, user_id: int | None = None) -> list[ChatMessage]:
    query = db.query(ChatMessage)
    if user_id is not None:
        query = (
            query.join(SessionRecord, ChatMessage.session_id == SessionRecord.id)
             .filter(SessionRecord.user_id == user_id)
        )
    else:
        query = query.filter(ChatMessage.session_id == session_id)
    return query.order_by(ChatMessage.timestamp.asc()).all() # type: ignore


def save_message(db: Session, session_id: str, role: str, content: str):
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg