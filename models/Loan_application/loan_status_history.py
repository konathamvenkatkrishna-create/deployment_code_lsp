from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class LoanStatusHistory(Base):
    __tablename__ = "loan_status_history"

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(
        Integer,
        ForeignKey("loan_application.id"),
        nullable=False
    )

    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    comment = Column(String, nullable=True)

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    # ✅ THIS LINE MUST EXIST (CRITICAL)
    loan_application = relationship(
        "LoanApplication",
        back_populates="status_history"
    )