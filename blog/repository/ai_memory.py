from sqlalchemy.orm import Session
from ..models import ChatMessage
from blog.models import SessionRecord

def create_session(db: Session, session_id: str, user_id:int = None):
    new_session = SessionRecord(id=session_id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

def get_session(db: Session, session_id: str):
    return db.query(SessionRecord).filter(SessionRecord.id == session_id).first()


def get_history(db: Session, session_id: str, user_id: int = None):
    query = db.query(ChatMessage)
    if user_id is not None:
        session_ids = db.query(SessionRecord.id).filter(SessionRecord.user_id == user_id).all()
        session_ids = [s.id for s in session_ids]
        query = query.filter(ChatMessage.session_id.in_(session_ids))
    else:
        query = query.filter(ChatMessage.session_id == session_id)
    return query.order_by(ChatMessage.timestamp.desc()).all()

def save_message(db: Session, session_id: str, role: str, content: str):
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg