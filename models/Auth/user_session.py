from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime, ForeignKey
from core.database import Base
from datetime import datetime


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = {"extend_existing": True}


    id = Column(BigInteger, primary_key=True)

    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    session_token = Column(Text, unique=True, nullable=False)
    refresh_token = Column(String, unique=True, nullable=False)

    device_id = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)