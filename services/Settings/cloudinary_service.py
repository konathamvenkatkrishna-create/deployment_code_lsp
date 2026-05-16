import os

import cloudinary
import cloudinary.uploader

from fastapi import HTTPException

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
# UPLOAD IMAGE
# =====================================================
def upload_image(

    file,

    folder: str = "uploads"
):

    try:

        # =============================================
        # VALIDATE FILE
        # =============================================
        if not file:

            raise HTTPException(

                status_code=400,

                detail="No file provided"
            )

        # =============================================
        # UPLOAD TO CLOUDINARY
        # =============================================
        result = cloudinary.uploader.upload(

            file,

            folder=folder,

            resource_type="image"
        )

        return {

            "success":
                True,

            "url":
                result.get("secure_url"),

            "public_id":
                result.get("public_id")
        }

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Image upload failed: {str(e)}"
        )


# =====================================================
# DELETE IMAGE
# =====================================================
def delete_image(

    public_id: str
):

    try:

        # =============================================
        # VALIDATE
        # =============================================
        if not public_id:

            raise HTTPException(

                status_code=400,

                detail="public_id is required"
            )

        # =============================================
        # DELETE FROM CLOUDINARY
        # =============================================
        result = cloudinary.uploader.destroy(
            public_id
        )

        return {

            "success":
                True,

            "result":
                result
        }

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Image delete failed: {str(e)}"
        )