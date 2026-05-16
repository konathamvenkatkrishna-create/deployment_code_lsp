from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime


class PreDisbursementResponseSchema(BaseModel):

    application_id: int
    lender_name: str
    approved_amount: Decimal = Field(
        ...,
        description="Approved loan amount")

    tenure_months: int

    interest_rate_percent: Decimal

    emi_amount: Decimal

    total_repayment: Decimal

    processing_fee: Decimal

    gst_amount: float

    total_processing_charges: Decimal

    disbursed_amount: Decimal

    class Config:
        from_attributes = True