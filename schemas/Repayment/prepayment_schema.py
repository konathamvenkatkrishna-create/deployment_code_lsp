from pydantic import (
    BaseModel,
    Field
)

from typing import (
    List
)

from datetime import date

from decimal import Decimal


# ======================================================
# EMI ITEM
# ======================================================
class PrepayEMIItem(BaseModel):

    emi_number: int

    due_date: date

    emi_amount: Decimal

    principal_component: Decimal

    interest_component: Decimal

    gst_amount: Decimal

    class Config:

        from_attributes = True

        json_encoders = {
            Decimal: lambda v: float(v)
        }


# ======================================================
# RESPONSE SCHEMA
# ======================================================
class PrepayResponse(BaseModel):

    application_id: int

    total_emis_selected: int = Field(
        ...,
        gt=0
    )

    emis: List[PrepayEMIItem]

    total_emi_amount: Decimal

    total_principal: Decimal

    total_interest: Decimal

    total_gst: Decimal

    prepay_penalty: Decimal

    penalty_gst: Decimal

    total_payable: Decimal

    currency: str = "INR"

    class Config:

        from_attributes = True

        # ======================================================
        # DECIMAL → JSON
        # ======================================================
        json_encoders = {
            Decimal: lambda v: float(v)
        }