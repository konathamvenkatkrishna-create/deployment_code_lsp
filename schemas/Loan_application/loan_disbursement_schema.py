from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional

from core.enums import (
    PaymentModeEnum,
    DisbursementStatusEnum
)


# =====================================================
# REQUEST: Disbursement
# =====================================================
class DisbursementRequestSchema(BaseModel):
    payment_mode: PaymentModeEnum = Field(
        ...,
        description="Select payout method (BANK or UPI)",
        example="BANK"
    )


# =====================================================
# RESPONSE: Disbursement
# =====================================================
class DisbursementResponseSchema(BaseModel):

    id: int = Field(
        ...,
        description="Disbursement record ID",
        example=1
    )

    application_id: int = Field(
        ...,
        description="Loan application ID",
        example=101
    )

    amount: Decimal = Field(
        ...,
        description="Net amount disbursed to user",
        example=15000.00
    )

    payment_mode: PaymentModeEnum = Field(
        ...,
        description="Selected payout method (BANK / UPI)",
        example="BANK"
    )

    payment_status: DisbursementStatusEnum = Field(
        ...,
        description="Current status of disbursement",
        example="SUCCESS"
    )

    payment_reference_id: Optional[str] = Field(
        None,
        description="Reference ID from payment gateway",
        example="RAZORPAY_123456"
    )

    payment_provider: Optional[str] = Field(
        None,
        description="Payment provider used",
        example="RAZORPAY"
    )

    failure_reason: Optional[str] = Field(
        None,
        description="Reason for failure (only if FAILED)",
        example="Bank server timeout"
    )

    initiated_at: Optional[datetime] = Field(
        None,
        description="Time when disbursement was initiated",
        example="2026-04-06T10:30:00Z"
    )

    completed_at: Optional[datetime] = Field(
        None,
        description="Time when disbursement was completed",
        example="2026-04-06T10:32:00Z"
    )

    retry_allowed: Optional[bool] = Field(
        None,
        description="True if retry is allowed (only when FAILED)",
        example=False
    )

    class Config:
        from_attributes = True
        use_enum_values = True