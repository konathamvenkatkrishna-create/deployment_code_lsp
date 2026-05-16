from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime
from core.database import Base

class ConsentMaster(Base):
    __tablename__ = "consent_master"

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    version = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)