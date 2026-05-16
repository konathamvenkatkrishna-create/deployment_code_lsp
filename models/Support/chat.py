from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from core.database import Base
from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import relationship




class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    sender = Column(String, default="user")  # user / agent
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_messages")



