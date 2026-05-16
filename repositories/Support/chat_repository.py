from sqlalchemy.orm import Session
from models.Support.chat import ChatMessage


def create_chat_message(db: Session, user_id: int, message: str, sender: str):
    chat = ChatMessage(
        user_id=user_id,
        message=message,
        sender=sender
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return chat


def get_chat_history_by_user(db: Session, user_id: int):
    return db.query(ChatMessage).filter(ChatMessage.user_id == user_id).all()