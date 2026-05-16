from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from core.database import get_db

from core.dependencies import (
    get_current_user
)

from models.Auth.user import User

from models.Settings.user_settings import (
    UserSettings,
    DeleteAccountRequest
)

from services.Settings.settings_service import (
    get_user_settings,
    update_user_settings
)

router = APIRouter(

    prefix="/settings",

    tags=["Settings"]
)


# =====================================================
# GET USER SETTINGS
# =====================================================
@router.get("/")
def fetch_settings(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    settings = get_user_settings(

        db,

        current_user.id
    )

    return {

        "success":
            True,

        "data":
            settings
    }


# =====================================================
# UPDATE USER SETTINGS
# =====================================================
@router.put("/")
def update_settings(

    payload: dict,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    settings = update_user_settings(

        db,

        current_user.id,

        payload
    )

    return {

        "success":
            True,

        "message":
            "Settings updated successfully",

        "data":
            settings
    }


# =====================================================
# DEACTIVATE USER
# =====================================================
@router.put("/deactivate")
def deactivate_user(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    current_user.status = "inactive"

    current_user.is_active = False

    db.add(current_user)

    db.commit()

    db.refresh(current_user)

    return {

        "success":
            True,

        "message":
            "User deactivated successfully"
    }


# =====================================================
# ACTIVATE USER
# =====================================================
@router.put("/activate")
def activate_user(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    current_user.status = "active"

    current_user.is_active = True

    db.add(current_user)

    db.commit()

    db.refresh(current_user)

    return {

        "success":
            True,

        "message":
            "User activated successfully"
    }


# =====================================================
# REQUEST DELETE ACCOUNT
# =====================================================
@router.post("/request-delete-account")
def request_delete_account(

    reason: str,

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
            reason,

        status=
            "pending"
    )

    db.add(request)

    db.commit()

    db.refresh(request)

    return {

        "success":
            True,

        "message":
            "Delete account request submitted",

        "data": {

            "request_id":
                request.id,

            "status":
                request.status
        }
    }


# =====================================================
# DELETE ACCOUNT
# ADMIN / FINAL DELETE
# =====================================================
@router.delete("/delete-account")
def delete_account(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    current_user.is_active = False

    current_user.status = "deleted"

    db.add(current_user)

    db.commit()

    return {

        "success":
            True,

        "message":
            "Account deleted successfully"
    }