from sqlalchemy import Column, Integer, Numeric, Date, String, ForeignKey
from core.database import Base
from sqlalchemy.orm import relationship

class EMISchedule(Base):
    __tablename__ = "emi_schedules"
    
    emi_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("loan_application.id"))
    emi_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    opening_principal = Column(Numeric(12, 2), nullable=False)
    principal_component = Column(Numeric(12, 2), nullable=False)
    interest_component = Column(Numeric(12, 2), nullable=False)
    gst_amount = Column(Numeric(12, 2), nullable=False)
    emi_amount = Column(Numeric(12, 2), nullable=False)
    closing_principal = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), default="DUE")

    # Relationship
    loan = relationship("LoanApplication", back_populates="emis")