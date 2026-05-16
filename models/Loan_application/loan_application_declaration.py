from sqlalchemy import Column, Boolean, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base


class LoanApplicationDeclaration(Base):
    __tablename__ = "loan_application_declaration"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(
        Integer,
        ForeignKey("loan_application.id", ondelete="CASCADE"),
        nullable=False,
        unique=True)

    agreed_terms = Column(Boolean, nullable=False)
    consent_credit_check = Column(Boolean, nullable=False)
    consent_data_sharing = Column(Boolean, nullable=False)
    has_existing_loans = Column(Boolean, nullable=False)
    has_credit_card = Column(Boolean, nullable=False)
    has_default_history = Column(Boolean, nullable=False)
    terms_version = Column(String(20), nullable=False)
    privacy_policy_version = Column(String(20), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    consent_timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    is_locked = Column(Boolean, default=False)

    loan_application = relationship(
        "LoanApplication",
        back_populates="declaration")
