from uuid import UUID
from datetime import datetime, date
from typing import Optional
from schemas.Loan_application.base import BaseSchema


class EMIScheduleSchema(BaseSchema):
    emi_id: Optional[UUID] = None 
    loan_id: UUID
    emi_number: int
    due_date: date
    principal_component: float
    interest_component: float
    gst_amount: float
    emi_amount: float
    status: str
    paid_on: Optional[datetime] = None
    overdue_days: Optional[int] = None
    penalty_amount: Optional[float] = None
