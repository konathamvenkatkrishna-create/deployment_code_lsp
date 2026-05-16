from sqlalchemy import Column, BigInteger, ForeignKey, String, DECIMAL
from sqlalchemy.orm import relationship
from core.database import Base


class CreditAccount(Base):
    __tablename__ = "credit_accounts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    credit_profile_id = Column(
        BigInteger,
        ForeignKey("credit_profiles.id"),
        nullable=False
    )
    loan_type  = Column(String(30), nullable=True)
    emi_amount = Column(DECIMAL(12, 2), default=0.00)
    status     = Column(String(20), nullable=True)
    credit_profile = relationship(
        "CreditProfile",
        back_populates="accounts"
    )