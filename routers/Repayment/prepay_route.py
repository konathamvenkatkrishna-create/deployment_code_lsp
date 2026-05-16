from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

import traceback

from core.database import get_db

from core.dependencies import (
    require_roles
)

from models.Auth.user import User

from schemas.Repayment.prepayment_schema import (
    PrepayResponse
)

from services.Repayment.prepay import (
    process_prepay
)


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(
    prefix="/prepayment",
    tags=["Prepayment"]
)


# =====================================================
# 🔥 PREPAYMENT SUMMARY ONLY
# =====================================================
@router.get(
    "/summary",

    response_model=PrepayResponse,

    status_code=status.HTTP_200_OK,

    summary=(
        "Get prepayment "
        "summary for current loan"
    )
)
def calculate_prepayment(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles("USER")
    )
):
    """

    This API ONLY shows prepayment summary.

    It DOES NOT:
    - initiate payment
    - create transaction
    - update EMI
    - update loan status


    - UI preview
    - foreclosure summary
    - partial prepayment summary


    1. Call this API
       → show total payable

    2. Frontend calls:
       /manual-payment/initiate

       with:
       payment_option=PREPAY

    3. User selects payment mode

    4. Razorpay payment happens

    5. Webhook updates:
       - EMI
       - payment status
       - loan status
    """

    try:

        # =====================================================
        # PREPAY SUMMARY ONLY
        # =====================================================
        response = process_prepay(

            db=db,

            user_id=current_user.id
        )

        return response

    except HTTPException as e:

        raise e

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception:

        print(
            "❌ PREPAY "
            "CALCULATION ERROR:"
        )

        print(
            traceback.format_exc()
        )

        raise HTTPException(

            status_code=500,

            detail=(
                "Internal server error"
            )
        )