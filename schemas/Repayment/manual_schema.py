from pydantic import BaseModel
from enum import Enum
from typing import Optional, List, Union
from datetime import datetime, date
from decimal import Decimal


# =====================================================
# PAYMENT MODE
# =====================================================
class PaymentModeEnum(str, Enum):
    UPI = "UPI"
    BANK_TRANSFER = "BANK_TRANSFER"
    CREDIT_CARD = "CREDIT_CARD"


# =====================================================
# PAYMENT OPTION 
# =====================================================
class PaymentOptionEnum(str, Enum):

    REGULAR = "REGULAR"

    PREPAY = "PREPAY"

    FORECLOSURE = "FORECLOSURE"


# =====================================================
# LENDER DETAILS
# =====================================================
class LenderUPIDetails(BaseModel):
    lender_upi: str
    lender_account_holder_name: str


class LenderBankTransferDetails(BaseModel):
    lender_account_holder_name: str
    lender_account_number: str
    ifsc: str
    lender_bank_name: str


class LenderCreditCardDetails(BaseModel):
    lender_account_holder_name: str
    lender_card_number: str
    lender_card_type: str
    lender_expiry: str


# =====================================================
# PAYMENT RESPONSE (🔥 UPDATED)
# =====================================================
class PaymentResponse(BaseModel):
    transaction_id: Optional[str]
    order_id: Optional[str]          # 🔥 Razorpay
    application_id: int
    emi_number: Optional[int]

    emi_amount: Decimal
    amount_paid: Decimal

    payment_mode: PaymentModeEnum    # 🔥 enum
    payment_option: PaymentOptionEnum  # 🔥 enum

    status: str                      # INITIATED / SUCCESS / FAILED
    date: datetime

    payment_details: Union[
        LenderUPIDetails,
        LenderBankTransferDetails,
        LenderCreditCardDetails
    ]

    class Config:
        from_attributes = True


# =====================================================
# DUES
# =====================================================
class DueEMIItem(BaseModel):
    emi_number: int
    emi_amount: Decimal
    due_date: Optional[date]
    status: str


class DuesResponse(BaseModel):
    application_id: int
    total_due_emis: int
    total_due_amount: Decimal
    due_emis: List[DueEMIItem]


# =====================================================
# OVERDUE
# =====================================================
class OverdueEMIItem(BaseModel):
    emi_number: int
    emi_amount: Decimal
    due_date: Optional[date]
    overdue_days: int
    status: str


class OverdueResponse(BaseModel):
    application_id: int
    overdue_count: int
    total_emi_amount: Decimal
    total_interest: Decimal
    penalty: Decimal
    penalty_gst: Decimal
    total_payable: Decimal
    overdue_emis: List[OverdueEMIItem]


class NoOverdueResponse(BaseModel):
    application_id: int
    message: str
    overdue_count: int
    penalty: Decimal
    penalty_gst: Decimal
    total_payable: Decimal