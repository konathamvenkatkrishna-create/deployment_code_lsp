from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from core.enums import LoanApplicationStep


class LoanApplicationStepCreate(BaseModel):
    application_id: int
    current_step: LoanApplicationStep | None = None

class LoanApplicationStepUpdate(BaseModel):
    loan_details_completed: Optional[bool] = None
    purpose_completed: Optional[bool] = None
    references_completed: Optional[bool] = None
    declaration_completed: Optional[bool] = None
    summary_viewed: Optional[bool] = None
    current_step: Optional[LoanApplicationStep] = None
    
class LoanApplicationStepResponse(BaseModel):
    loan_details_completed: bool
    purpose_completed: bool
    references_completed: bool
    declaration_completed: bool
    summary_viewed: bool
    current_step: LoanApplicationStep | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StepCompletionCheck(BaseModel):
    loan_details_completed: bool
    purpose_completed: bool
    references_completed: bool
    declaration_completed: bool
    summary_viewed: bool
    all_steps_completed: bool