from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from schemas.Repayment.auto_debit_schema import PaymentModeEnum, PaymentOptionEnum
from services.Repayment.auto_debit_payment import process_auto_debit


router = APIRouter(prefix="/auto-debit", tags=["Payments"])


@router.post("/pay")
async def auto_debit_payment(   # ✅ async added
    payment_mode: PaymentModeEnum,
    payment_option: PaymentOptionEnum,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    """
    Auto debit EMI for current user's ACTIVE loan
    """

    try:
        result = process_auto_debit(
            db=db,
            user_id=current_user.id,
            payment_mode=payment_mode,
            payment_option=payment_option,
        )

        return {
            "success": True,
            "data": result
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))