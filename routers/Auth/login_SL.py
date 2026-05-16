
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from core.database import get_db
from models.Auth.user import User
from core.security import (
    verify_password,
    create_access_token,
    create_refresh_token
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    user = db.query(User).filter(
        User.mobile_number == form_data.username
    ).first()

    # ❌ User not found
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Please register first"
        )

    # ❌ Wrong password
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect password"
        )

    # ❌ Not active
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account not activated"
        )

    # ❌ Not verified
    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify OTP first"
        )

    # ✅ SUCCESS → INCLUDE ROLE
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role   # 🔥 IMPORTANT FIX
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "role": user.role
        }
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role
    }

