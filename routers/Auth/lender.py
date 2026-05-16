from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from models.Auth.lender import Lender
from models.Auth.user import User
from schemas.Auth.lenderregisterschema import LenderCreate, LenderResponse, LenderUpdate
from services.Auth.superadminservices import super_admin_required, lender_required
from core.security import hash_password
from core.validators import validate_mobile_number, validate_password
from core.dependencies import get_current_user
router = APIRouter(
    prefix="/lenders",
    tags=["SuperAdmin Lenders"]
)


@router.post(
    "/create",
    response_model=LenderResponse,
    status_code=status.HTTP_201_CREATED,
    name="admin_create_lender"
)
def create_lender(
    lender_data: LenderCreate,
    db: Session = Depends(get_db),
    superadmin = Depends(super_admin_required),
):
    validate_mobile_number(lender_data.mobile_number)
    validate_password(lender_data.password)

    existing_user = db.query(User).filter(
        User.mobile_number == lender_data.mobile_number,
        User.role == "LENDER"
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        mobile_number=lender_data.mobile_number,
        username=lender_data.company_name.lower(),
        password_hash=hash_password(lender_data.password),
        role="LENDER",
        device_id="lender-device",
        is_verified = True,
        is_active = True,
    )

    db.add(user)
    db.flush()  

    lender = Lender(
        user_id=user.id,
        company_name=lender_data.company_name,
        gst_number=lender_data.gst_number,
        address=lender_data.address,

        min_credit_score=lender_data.min_credit_score,
        max_amount=lender_data.max_amount,
        interest_rate=lender_data.interest_rate,
        processing_fee=lender_data.processing_fee,
        benefits=lender_data.benefits,
        created_by=superadmin.id,     
        updated_by=superadmin.id,
        is_active=True,
        is_verified=True,
        is_blocked=False,
        )

    db.add(lender)
    db.commit()
    db.refresh(lender)

    return lender


# ======================================================
# UPDATE LENDER
# ======================================================
@router.put(
    "/update/{company_name}",
    response_model=LenderResponse,
    name="admin_update_lender"
)
def update_lender(
    company_name: str,
    lender_data: LenderUpdate,
    db: Session = Depends(get_db),
    superadmin = Depends(super_admin_required),
):
    lender = db.query(Lender).join(User).filter(
        Lender.company_name == company_name,
        User.role == "LENDER"
    ).first()

    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")

    update_data = lender_data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(lender, key, value)

    if "company_name" in update_data:
        new_name = update_data["company_name"].lower().strip()
        lender.user.username = new_name
        lender.company_name = new_name
    lender.updated_by = superadmin.id
    db.commit()
    db.refresh(lender)

    return lender


# ======================================================
# DELETE LENDER
# ======================================================
@router.delete(
    "/delete/{company_name}",
    name="admin_delete_lender"
)
def delete_lender(
    company_name: str,
    db: Session = Depends(get_db),
    superadmin = Depends(super_admin_required),
):
    lender = db.query(Lender).join(User).filter(
        Lender.company_name == company_name,
        User.role == "LENDER"
    ).first()

    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")

    user_id = lender.user_id

    db.delete(lender)
    db.commit()

    db.query(User).filter(User.id == user_id).delete()
    db.commit()

    return {
        "message": "Lender deleted successfully",
        "id": lender.id,
        "company_name": lender.company_name,
    }
