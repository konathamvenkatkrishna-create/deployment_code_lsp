from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from core.database import (
    get_db
)

from models.Auth.user import (
    User
)

from core.security import (
    hash_password
)

from core.validators import (

    validate_password,

    validate_mobile_number
)

from services.Auth.superadminservices import (
    super_admin_required
)

from schemas.Auth.support import (

    CreateSupportUserSchema,

    UpdateSupportUserSchema
)


# =====================================================
# CONSTANTS
# =====================================================
ROLE_SUPPORT = "SUPPORT"

DEVICE_ID = "SUPPORT-ID"


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(

    tags=["SuperAdmin | Support Team"]
)


# =====================================================
# CREATE SUPPORT USER
# =====================================================
@router.post(
    "/support/create",

    status_code=status.HTTP_201_CREATED
)
def create_support_user(

    payload: CreateSupportUserSchema,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        super_admin_required
    ),
):

    # =============================================
    # VALIDATE PASSWORD
    # =============================================
    validate_password(
        payload.password
    )

    # =============================================
    # VALIDATE MOBILE
    # =============================================
    mobile = validate_mobile_number(
        payload.mobile
    )

    # =============================================
    # CHECK MOBILE EXISTS
    # =============================================
    existing_mobile = db.query(User).filter(
        User.mobile_number == mobile
    ).first()

    if existing_mobile:

        raise HTTPException(

            status_code=status.HTTP_409_CONFLICT,

            detail="Mobile number already exists"
        )

    # =============================================
    # CHECK USERNAME EXISTS
    # =============================================
    existing_username = db.query(User).filter(
        User.username == payload.username
    ).first()

    if existing_username:

        raise HTTPException(

            status_code=status.HTTP_409_CONFLICT,

            detail="Username already exists"
        )

    # =============================================
    # CREATE SUPPORT USER
    # =============================================
    support_user = User(

        username=
            payload.username,

        mobile_number=
            mobile,

        password_hash=
            hash_password(payload.password),

        device_id=
            DEVICE_ID,

        role=
            ROLE_SUPPORT,

        is_active=
            True,

        is_verified=
            True,
    )

    db.add(support_user)

    db.commit()

    db.refresh(support_user)

    return {

        "message":
            "Support team user created successfully",

        "user": {

            "id":
                support_user.id,

            "username":
                support_user.username,

            "mobile":
                support_user.mobile_number,

            "role":
                support_user.role,
        },
    }


# =====================================================
# GET ALL SUPPORT USERS
# =====================================================
@router.get("/support")
def get_all_support_users(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        super_admin_required
    ),
):

    users = db.query(User).filter(
        User.role == ROLE_SUPPORT
    ).all()

    return {

        "count":
            len(users),

        "users": [

            {

                "id":
                    u.id,

                "username":
                    u.username,

                "mobile":
                    u.mobile_number,

                "is_active":
                    u.is_active,
            }

            for u in users
        ],
    }


# =====================================================
# GET SUPPORT USER BY MOBILE
# =====================================================
@router.get("/support/by-mobile/{mobile_number}")
def get_support_user_by_mobile(

    mobile_number: str,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        super_admin_required
    ),
):

    mobile = validate_mobile_number(
        mobile_number
    )

    user = db.query(User).filter(

        User.mobile_number == mobile,

        User.role == ROLE_SUPPORT

    ).first()

    if not user:

        raise HTTPException(

            status_code=404,

            detail="Support user not found"
        )

    return {

        "id":
            user.id,

        "username":
            user.username,

        "mobile":
            user.mobile_number,

        "is_active":
            user.is_active,

        "role":
            user.role,
    }


# =====================================================
# UPDATE SUPPORT USER
# =====================================================
@router.put("/support/by-mobile/{mobile_number}")
def update_support_user(

    mobile_number: str,

    payload: UpdateSupportUserSchema,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        super_admin_required
    ),
):

    mobile = validate_mobile_number(
        mobile_number
    )

    user = db.query(User).filter(

        User.mobile_number == mobile,

        User.role == ROLE_SUPPORT

    ).first()

    if not user:

        raise HTTPException(

            status_code=404,

            detail="Support user not found"
        )

    update_data = payload.dict(
        exclude_unset=True
    )

    if not update_data:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail="No valid fields provided for update"
        )

    # =============================================
    # UPDATE PASSWORD
    # =============================================
    if "password" in update_data:

        validate_password(
            update_data["password"]
        )

        user.password_hash = hash_password(
            update_data.pop("password")
        )

    # =============================================
    # UPDATE MOBILE
    # =============================================
    if "mobile" in update_data:

        new_mobile = validate_mobile_number(
            update_data["mobile"]
        )

        exists = db.query(User).filter(

            User.mobile_number == new_mobile,

            User.id != user.id

        ).first()

        if exists:

            raise HTTPException(

                status_code=status.HTTP_409_CONFLICT,

                detail="Mobile number already exists"
            )

        user.mobile_number = new_mobile

        update_data.pop("mobile")

    # =============================================
    # UPDATE OTHER FIELDS
    # =============================================
    for field, value in update_data.items():

        setattr(
            user,
            field,
            value
        )

    db.commit()

    db.refresh(user)

    return {

        "message":
            "Support user updated successfully",

        "user": {

            "id":
                user.id,

            "username":
                user.username,

            "mobile":
                user.mobile_number,

            "is_active":
                user.is_active,
        },
    }


# =====================================================
# DELETE SUPPORT USER
# =====================================================
@router.delete(
    "/support/by-mobile/{mobile_number}",

    status_code=status.HTTP_204_NO_CONTENT
)
def delete_support_user(

    mobile_number: str,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        super_admin_required
    ),
):

    mobile = validate_mobile_number(
        mobile_number
    )

    user = db.query(User).filter(

        User.mobile_number == mobile,

        User.role == ROLE_SUPPORT

    ).first()

    if not user:

        raise HTTPException(

            status_code=404,

            detail="Support user not found"
        )

    db.delete(user)

    db.commit()

    return {

        "message":
            "Support user deleted successfully"
    }