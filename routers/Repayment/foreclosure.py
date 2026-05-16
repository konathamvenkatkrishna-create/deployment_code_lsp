from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from core.database import get_db

from core.dependencies import (
    require_roles
)

from models.Auth.user import User

from services.Repayment.foreclosure import (
    create_foreclosure_request
)


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(
    prefix="/foreclosure",
    tags=["Foreclosure"]
)


# =====================================================
# 🔥 CREATE FORECLOSURE SUMMARY
# =====================================================
@router.post("/request")
def create_foreclosure(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles("USER")
    )
):
    """
    =====================================================
    PURPOSE
    =====================================================

    Generates foreclosure summary
    for current ACTIVE loan.

    =====================================================
    THIS API DOES
    =====================================================

    ✔ Calculates:
      - pending amount
      - foreclosure charges
      - GST
      - final payable amount

    ✔ Creates foreclosure request

    ✔ Stores foreclosure snapshot

    =====================================================
    THIS API DOES NOT
    =====================================================

    ✘ initiate payment
    ✘ close loan
    ✘ update EMI
    ✘ mark payment SUCCESS

    =====================================================
    NEXT FLOW
    =====================================================

    1. User checks foreclosure summary

    2. Frontend calls:
       /manual-payment/initiate

       with:
       payment_option=FORECLOSURE

    3. Payment initiated

    4. Webhook receives:
       payment.captured

    5. System automatically:
       ✔ marks payment SUCCESS
       ✔ marks all EMIs PAID
       ✔ closes loan
    """

    try:

        result = create_foreclosure_request(

            db=db,

            user_id=current_user.id
        )

        return {

            "success": True,

            "message":
                "Foreclosure summary generated successfully",

            "data": result
        }

    except HTTPException as e:

        raise e

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )