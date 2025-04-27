from sqlalchemy.orm import Session
from ..models import ChatMessage
from blog.models import SessionRecord

def create_session(db: Session, session_id: str):
    new_session = SessionRecord(id=session_id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

def get_session(db: Session, session_id: str):
    return db.query(SessionRecord).filter(SessionRecord.id == session_id).first()


def get_history(db:Session, session_id: str):
    return(
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp.desc())
        .all()
    )
def save_message(db: Session, session_id: str, role: str, content: str):
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg