from sqlalchemy import Column, BigInteger, String, Text, DateTime
from datetime import datetime
from core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    action = Column(String(100), nullable=False)
    user_id = Column(BigInteger, nullable=False)  # FIXED to BigInteger
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
