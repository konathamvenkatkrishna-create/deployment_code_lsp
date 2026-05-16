from fastapi import (
    APIRouter,
    Body,
    Depends,
    UploadFile,
    File,
    HTTPException
)

from sqlalchemy.orm import Session

from pydantic import (
    BaseModel,
    EmailStr
)

from core.dependencies import (
    get_current_user
)

from core.database import (
    get_db
)

from models.Auth.user_session import (
    UserSession
)

from models.Auth.user import (
    User
)

from models.Profile_KYC.user_profile import (
    UserProfile
)

from models.Settings.user_settings import (
    DeleteAccountRequest
)

from schemas.Settings.common_response import (
    CommonResponse
)

from schemas.Settings.profile_schema import (

    ProfileUpdate,

    TempAddressUpdate
)

from services.Settings.cloudinary_service import (
    upload_image
)

from services.Settings.profile_service import (

    update_user_profile,

    delete_user_account,

    send_otp_to_old_email,

    verify_otp_and_update_email
)


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(

    prefix="/user/profile",

    tags=["Profile"]
)


# =====================================================
# EMAIL UPDATE SCHEMA
# =====================================================
class UpdateEmail(BaseModel):

    new_email: EmailStr

    otp: str


# =====================================================
# GET PROFILE
# =====================================================
@router.get("/")
def get_profile(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    profile = db.query(
        UserProfile
    ).filter(
        UserProfile.user_id
        == current_user.id
    ).first()

    if not profile:

        raise HTTPException(

            status_code=404,

            detail="Profile not found"
        )

    return {

        "success":
            True,

        "data":
            profile
    }


# =====================================================
# UPDATE PROFILE
# =====================================================
@router.put(
    "/",

    response_model=CommonResponse
)
def update_profile(

    data: ProfileUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    profile = update_user_profile(

        db=db,

        user=current_user,

        data=data.dict(
            exclude_unset=True
        )
    )

    return CommonResponse(

        success=True,

        message="Profile updated successfully",

        data=profile
    )


# =====================================================
# UPDATE TEMP ADDRESS
# =====================================================
@router.put("/temp-address")
def update_temp_address(

    data: TempAddressUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    profile = db.query(
        UserProfile
    ).filter(
        UserProfile.user_id
        == current_user.id
    ).first()

    if not profile:

        raise HTTPException(

            status_code=404,

            detail="Profile not found"
        )

    profile.temporary_address = (
        data.temporary_address
    )

    db.add(profile)

    db.commit()

    db.refresh(profile)

    return {

        "success":
            True,

        "message":
            "Temporary address updated successfully",

        "temporary_address":
            profile.temporary_address
    }


# =====================================================
# SEND EMAIL OTP
# =====================================================
@router.post(
    "/send-email-otp",

    response_model=CommonResponse
)
def send_email_otp(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    result = send_otp_to_old_email(

        db=db,

        user=current_user
    )

    return CommonResponse(

        success=True,

        message=result["message"],

        data=None
    )


# =====================================================
# UPDATE EMAIL
# =====================================================
@router.put(
    "/update-email",

    response_model=CommonResponse
)
def update_email(

    payload: UpdateEmail,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    result = verify_otp_and_update_email(

        db=db,

        user=current_user,

        new_email=payload.new_email,

        otp=payload.otp
    )

    return CommonResponse(

        success=True,

        message=result["message"],

        data={

            "email":
                result["email"]
        }
    )


# =====================================================
# ACTIVE SESSIONS
# =====================================================
@router.get("/active-sessions")
def active_sessions(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    sessions = db.query(
        UserSession
    ).filter(

        UserSession.user_id
        == current_user.id,

        UserSession.is_active
        == True

    ).all()

    return {

        "success":
            True,

        "count":
            len(sessions),

        "data":
            sessions
    }


# =====================================================
# LOGOUT ALL DEVICES
# =====================================================
@router.post("/logout-all")
def logout_all(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    db.query(
        UserSession
    ).filter(

        UserSession.user_id
        == current_user.id,

        UserSession.is_active
        == True

    ).update({

        "is_active": False
    })

    db.commit()

    return {

        "success":
            True,

        "message":
            "Logged out from all devices"
    }


# =====================================================
# UPLOAD PROFILE IMAGE
# =====================================================
@router.post("/upload-dp")
async def upload_dp(

    file: UploadFile = File(...),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    # =============================================
    # FILE TYPE VALIDATION
    # =============================================
    if file.content_type not in [

        "image/jpeg",

        "image/png",

        "image/jpg"
    ]:

        raise HTTPException(

            status_code=400,

            detail="Only JPG/PNG allowed"
        )

    profile = db.query(
        UserProfile
    ).filter(
        UserProfile.user_id
        == current_user.id
    ).first()

    if not profile:

        raise HTTPException(

            status_code=404,

            detail="Profile not found"
        )

    # =============================================
    # UPLOAD IMAGE
    # =============================================
    result = upload_image(
        file.file
    )

    profile.profile_image_url = (
        result["secure_url"]
        if "secure_url" in result
        else result["url"]
    )

    db.add(profile)

    db.commit()

    db.refresh(profile)

    return {

        "success":
            True,

        "message":
            "Profile image uploaded successfully",

        "url":
            profile.profile_image_url
    }


# =====================================================
# DELETE PROFILE IMAGE
# =====================================================
@router.delete("/delete-dp")
async def delete_dp(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    profile = db.query(
        UserProfile
    ).filter(
        UserProfile.user_id
        == current_user.id
    ).first()

    if not profile:

        raise HTTPException(

            status_code=404,

            detail="Profile not found"
        )

    if not profile.profile_image_url:

        raise HTTPException(

            status_code=400,

            detail="No profile image found"
        )

    profile.profile_image_url = None

    db.add(profile)

    db.commit()

    return {

        "success":
            True,

        "message":
            "Profile image deleted successfully"
    }


# =====================================================
# DELETE ACCOUNT REQUEST
# =====================================================
@router.post(
    "/request-delete-account",

    response_model=CommonResponse
)
def request_delete_account(

    reason: str = Body(...),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    existing = db.query(
        DeleteAccountRequest
    ).filter(

        DeleteAccountRequest.user_id
        == current_user.id,

        DeleteAccountRequest.status
        == "pending"

    ).first()

    if existing:

        raise HTTPException(

            status_code=400,

            detail="Delete request already pending"
        )

    request = DeleteAccountRequest(

        user_id=
            current_user.id,

        reason=
            reason
    )

    db.add(request)

    db.commit()

    return CommonResponse(

        success=True,

        message="Delete request sent successfully",

        data=None
    )