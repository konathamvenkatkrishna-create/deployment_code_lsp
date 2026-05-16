from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from services.Repayment.emi_schedule import generate_emi_schedule_service


router = APIRouter(
    prefix="/emis",
    tags=["EMI Schedule"]
)


@router.post("/generate")
def generate_emi_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    """
    Generate EMI schedule for current user's ACTIVE loan
    """

    return generate_emi_schedule_service(
        current_user_id=current_user.id,
        db=db
    )