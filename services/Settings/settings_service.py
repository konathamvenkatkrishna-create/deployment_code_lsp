from sqlalchemy.orm import Session

from fastapi import HTTPException

from models.Settings.user_settings import (
    UserSettings
)


# =====================================================
# GET USER SETTINGS
# =====================================================
def get_user_settings(

    db: Session,

    user_id: int
):

    settings = db.query(
        UserSettings
    ).filter(
        UserSettings.user_id
        == user_id
    ).first()

    # =================================================
    # CREATE DEFAULT SETTINGS
    # =================================================
    if not settings:

        settings = UserSettings(

            user_id=
                user_id
        )

        db.add(settings)

        db.commit()

        db.refresh(settings)

    return settings


# =====================================================
# UPDATE USER SETTINGS
# =====================================================
def update_user_settings(

    db: Session,

    user_id: int,

    data: dict
):

    # =================================================
    # FETCH SETTINGS
    # =================================================
    settings = db.query(
        UserSettings
    ).filter(
        UserSettings.user_id
        == user_id
    ).first()

    # =================================================
    # CREATE DEFAULT SETTINGS
    # =================================================
    if not settings:

        settings = UserSettings(

            user_id=
                user_id
        )

        db.add(settings)

        db.commit()

        db.refresh(settings)

    # =================================================
    # ALLOWED FIELDS ONLY
    # =================================================
    allowed_fields = [

        "theme",

        "language",

        "notifications_enabled",

        "email_notifications",

        "sms_notifications",

        "dark_mode",

        "biometric_login"
    ]

    # =================================================
    # UPDATE SETTINGS
    # =================================================
    for key, value in data.items():

        if key not in allowed_fields:

            raise HTTPException(

                status_code=400,

                detail=f"Invalid setting field: {key}"
            )

        if hasattr(settings, key):

            setattr(
                settings,
                key,
                value
            )

    # =================================================
    # SAVE
    # =================================================
    db.add(settings)

    db.commit()

    db.refresh(settings)

    return settings