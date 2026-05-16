from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database import get_db
from models.Auth.user import User
from models.Settings.user_session import UserSession
from models.Settings.user_settings import DeleteAccountRequest
from services.Auth.superadminservices import super_admin_required
from core.validators import validate_mobile_number
from schemas.Auth.SendOTPSchema import  UpdateUserSchema
router = APIRouter(
    prefix="/auth",
    tags=["SuperAdmin Access"]
)
# ======================================================
# ADMIN — GET USERS
# ======================================================

@router.get("/users/by-mobile/{mobile_number}")
def get_user_by_mobile(
    mobile_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(super_admin_required),
):
    validate_mobile_number(mobile_number)

    user = db.query(User).filter(
        User.mobile_number == mobile_number,User.role == "USER"
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "mobile_number": user.mobile_number,
        "username": user.username,
        "role": user.role,
        "device_id": user.device_id,
    }

# ADMIN — GET USERS
@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(super_admin_required),
):
    users = db.query(User).filter(User.role == "USER").all()

    return {
        "count": len(users),
        "users": [
            {
                "id": u.id,
                "mobile_number": u.mobile_number,
                "username": u.username,
                "role": u.role,
                "device_id": u.device_id,
            }
            for u in users
        ],
    }

# ADMIN - DELETE USER BY MOBILE
@router.delete(
    "/users/by-mobile/{mobile_number}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_user_by_mobile(
    mobile_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(super_admin_required),
):
    validate_mobile_number(mobile_number)

    user = db.query(User).filter(
        User.mobile_number == mobile_number,User.role == "USER"
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# ADMIN - UPDATE USER BY MOBILE
@router.put(
    "/users/by-mobile/{mobile_number}",
    status_code=status.HTTP_200_OK
)
def update_user_by_mobile(
    mobile_number: str,
    payload: UpdateUserSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(super_admin_required),
):
    validate_mobile_number(mobile_number)

    #  Find existing user
    user = db.query(User).filter(
        User.mobile_number == mobile_number,User.role == "USER"
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    update_data = payload.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update"
        )

    #  IF mobile_number is being updated
    if "mobile_number" in update_data:
        new_mobile = update_data["mobile_number"]
        validate_mobile_number(new_mobile)

        #  Check if new mobile already exists for another user
        existing_user = (
            db.query(User)
            .filter(
                User.mobile_number == new_mobile,
                User.id != user.id   
            )
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Mobile number already exists"
            )

    #  Apply updates safely
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return {
        "message": "User updated successfully",
        "user": {
            "id": user.id,
            "mobile_number": user.mobile_number,
            "username": user.username,
            "device_id": user.device_id
        }
    }
# ======================================================
# 🔥 ADMIN — GET DELETE ACCOUNT REQUESTS
# ======================================================
@router.get("/admin/delete-requests")
def get_delete_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(super_admin_required),
):
    requests = db.query(DeleteAccountRequest).all()

    return {
        "count": len(requests),
        "requests": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "reason": r.reason,
                "status": r.status,
                "created_at": r.created_at
            }
            for r in requests
        ]
    }


# ======================================================
# 🔥 ADMIN — APPROVE / REJECT DELETE REQUEST
# ======================================================
@router.put("/admin/delete-request/{request_id}")
def handle_delete_request(
    request_id: int,
    status: str,  # approved / rejected
    db: Session = Depends(get_db),
    current_user: User = Depends(super_admin_required)
):
    req = db.query(DeleteAccountRequest).filter(
        DeleteAccountRequest.id == request_id
    ).first()

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Already processed")

    if status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    req.status = status

    # ✅ If approved → delete user
    if status == "approved":
        user = db.query(User).filter(User.id == req.user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=400, detail="User already deleted")

        # 🔐 Soft delete
        user.is_active = False

        # 🔐 Logout sessions
        db.query(UserSession).filter(
            UserSession.user_id == user.id
        ).update({"is_active": False})

    db.commit()

    return {"message": f"Request {status}"}