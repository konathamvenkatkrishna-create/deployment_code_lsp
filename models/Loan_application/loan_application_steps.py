from sqlalchemy import Column, Boolean, TIMESTAMP, ForeignKey, String, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base


class LoanApplicationStepTracker(Base):
    __tablename__ = "loan_application_step_tracker"

    application_id = Column(
        Integer,
        ForeignKey("loan_application.id", ondelete="CASCADE"),
        primary_key=True)
    loan_details_completed = Column(Boolean, default=True)
    purpose_completed = Column(Boolean, default=False)
    references_completed = Column(Boolean, default=False)
    declaration_completed = Column(Boolean, default=False)
    current_step = Column(String(50), nullable=False)
    last_completed_step = Column(String(50), nullable=True)
    is_fraud_suspected = Column(Boolean, default=False)
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now())

    loan_application = relationship(
        "LoanApplication",
        back_populates="step_tracker")
