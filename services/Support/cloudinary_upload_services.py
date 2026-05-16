import re
import uuid
import os

import cloudinary
import cloudinary.uploader

from fastapi import (
    UploadFile,
    HTTPException
)

from core.config import settings


# =====================================================
# CLOUDINARY CONFIG
# =====================================================
cloudinary.config(

    cloud_name=
        settings.CLOUDINARY_CLOUD_NAME,

    api_key=
        settings.CLOUDINARY_API_KEY,

    api_secret=
        settings.CLOUDINARY_API_SECRET,

    secure=True
)


# =====================================================
# CONFIG
# =====================================================
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB


ALLOWED_CONTENT_TYPES = [

    "image/jpeg",

    "image/png",

    "image/jpg",

    "application/pdf",
]


# =====================================================
# CLEAN CATEGORY NAME
# =====================================================
def clean_folder_name(
    value: str
) -> str:

    """
    Converts:
    Login Issue -> LOGIN_ISSUE
    """

    value = value.strip().upper()

    value = re.sub(
        r"[^A-Z0-9]+",
        "_",
        value
    )

    return value.strip("_")


# =====================================================
# VALIDATE FILE
# =====================================================
def validate_attachment(

    attachment: UploadFile,

    content: bytes
):

    # =============================================
    # EMPTY FILE
    # =============================================
    if not content:

        raise HTTPException(

            status_code=400,

            detail="Attachment file is empty"
        )

    # =============================================
    # FILE SIZE VALIDATION
    # =============================================
    if len(content) > MAX_FILE_SIZE:

        raise HTTPException(

            status_code=400,

            detail="Attachment size must be <= 2 MB"
        )

    # =============================================
    # FILE TYPE VALIDATION
    # =============================================
    if attachment.content_type not in ALLOWED_CONTENT_TYPES:

        raise HTTPException(

            status_code=400,

            detail=(
                "Only JPG, PNG, PDF "
                "files are allowed"
            )
        )


# =====================================================
# MAIN UPLOAD FUNCTION
# =====================================================
async def upload_support_attachment(

    attachment: UploadFile,

    category: str,

    user_id: int,

    complaint_id: int,
) -> str:

    # =============================================
    # READ FILE
    # =============================================
    content = await attachment.read()

    # =============================================
    # VALIDATE FILE
    # =============================================
    validate_attachment(
        attachment,
        content
    )

    # =============================================
    # SAFE FILE NAME
    # =============================================
    original_filename = os.path.basename(
        attachment.filename
    )

    safe_filename = re.sub(
        r"[^a-zA-Z0-9_.-]",
        "_",
        original_filename
    )

    unique_filename = (
        f"{uuid.uuid4()}_{safe_filename}"
    )

    # =============================================
    # CLEAN CATEGORY
    # =============================================
    folder_category = clean_folder_name(
        category
    )

    # =============================================
    # CLOUDINARY FOLDER
    # =============================================
    folder_path = (

        f"support_attachment_files/"
        f"{folder_category}/"
        f"user_{user_id}/"
        f"complaint_{complaint_id}"
    )

    try:

        # =========================================
        # UPLOAD TO CLOUDINARY
        # =========================================
        result = cloudinary.uploader.upload(

            content,

            folder=
                folder_path,

            resource_type=
                "auto",

            public_id=
                unique_filename,

            overwrite=
                False
        )

        secure_url = result.get(
            "secure_url"
        )

        if not secure_url:

            raise HTTPException(

                status_code=500,

                detail=(
                    "Cloudinary did not "
                    "return file URL"
                )
            )

        return secure_url

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=(
                f"Cloudinary upload failed: "
                f"{str(e)}"
            )
        )