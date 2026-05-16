from sqlalchemy import Column, Enum, String, ForeignKey, Integer
from sqlalchemy.orm import relationship
from core.database import Base
from core.enums import LoanPurpose


class LoanApplicationPurpose(Base):
    __tablename__ = "loan_application_purpose"

    application_id = Column(
        Integer,
        ForeignKey("loan_application.id", ondelete="CASCADE"),
        primary_key=True)

    purpose_code = Column(
        Enum(LoanPurpose, name="loan_purpose_enum"),
        nullable=False)
    purpose_description = Column(String(500))
    
    loan_application = relationship(
        "LoanApplication",
        back_populates="purpose")
