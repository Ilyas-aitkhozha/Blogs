from sqlalchemy.orm import Session
from tickets.models import SessionRecord, ChatMessage
import logging
import uuid
logger = logging.getLogger(__name__)

#getting latest session, or creating if exist
def get_or_create_session(db: Session, user_id: int) -> SessionRecord:
    session = (
        db.query(SessionRecord)
        .filter(SessionRecord.user_id == user_id)
        .order_by(SessionRecord.created_at.desc())
        .first()
    )
    if session:
        return session
    new_session_id = str(uuid.uuid4())
    new_session = SessionRecord(id=new_session_id, user_id=user_id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


def get_session(db: Session, session_id: str):
    return db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
#we are getting history of dialogue, context window in another words
def get_history(db: Session, session_id: str, user_id: int | None = None) -> list[ChatMessage]:
    query = db.query(ChatMessage)
    if user_id is not None:
        query = (
            query.join(SessionRecord, ChatMessage.session_id == SessionRecord.id) #below how i did in pgadmin, just making viborku less
             .filter(SessionRecord.user_id == user_id)#select s.user_id from sessions s join chat_messages c on c.session_id = s.id where s.user_id = 2
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