from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from core.database import Base


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)

    device_name = Column(String, default="web")
    ip_address = Column(String)
    login_time = Column(DateTime, default=datetime.utcnow)

    is_active = Column(Boolean, default=True)