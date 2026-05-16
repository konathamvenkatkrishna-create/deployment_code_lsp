from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import (
    Session
)

from pydantic import (
    BaseModel,
    Field
)

from core.database import (
    get_db
)

from core.dependencies import (
    get_current_user
)

from models.Auth.user import (
    User
)

from services.Profile_KYC.email_verify_service import (

    send_email_verification_otp,

    verify_email_otp
)


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(

    prefix="/email-verification",

    tags=["Email Verification"]
)


# =====================================================
# REQUEST SCHEMA
# =====================================================
class VerifyEmailOTPRequest(
    BaseModel
):

    otp: str = Field(
        ...,
        min_length=6,
        max_length=6
    )


# =====================================================
# SEND OTP
# =====================================================
@router.post("/send-otp")
def send_email_otp(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    try:

        result = send_email_verification_otp(

            db=db,

            user_id=current_user.id
        )

        return {

            "success":
                True,

            "message":
                result["message"],

            "data":
                result
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# =====================================================
# RESEND OTP
# =====================================================
@router.post("/resend-otp")
def resend_email_otp(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    try:

        result = send_email_verification_otp(

            db=db,

            user_id=current_user.id
        )

        return {

            "success":
                True,

            "message":
                "OTP resent successfully",

            "data":
                result
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# =====================================================
# VERIFY OTP
# =====================================================
@router.post("/verify-otp")
def verify_email_otp_api(

    payload: VerifyEmailOTPRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    try:

        result = verify_email_otp(

            db=db,

            user_id=current_user.id,

            otp=payload.otp
        )

        return {

            "success":
                True,

            "message":
                result["message"],

            "data":
                result
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )