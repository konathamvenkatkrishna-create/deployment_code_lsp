from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FinancialSummary(BaseModel):
    incomeConsidered: float
    existingEmi:      float
    proposedEmi:      float
    foir:             float
    allowedFoir:      float
    maxEligibleEmi:   float

class CreditSummary(BaseModel):
    currentScore:  Optional[int] = None
    previousScore: Optional[int] = None
    bureau:        Optional[str] = None

class CreditScoreTier(BaseModel):
    minScore:      int
    maxLoanAmount: int
    label:         str

class AmortizationRow(BaseModel):
    month:     int
    emi:       float
    principal: float
    interest:  float
    balance:   float

class TenureSchedule(BaseModel):
    tenureMonths: int
    emi:          float
    schedule:     list[AmortizationRow]

class EligibilityResultResponseExtended(BaseModel):
    status:  str
    message: str
    maxEligibleAmount:       Optional[float] = None
    
    

    class Config:
        from_attributes = True