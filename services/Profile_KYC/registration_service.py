from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from repositories.Profile_KYC.user_repository import UserRepository
from models.Profile_KYC.user_profile import UserProfile
from schemas.Profile_KYC.user_profile_schema import UserRegistrationRequest

class RegistrationService:

    # =====================================================
    # CREATE PROFILE
    # =====================================================
    @staticmethod
    def create_profile( db: Session, user_id: int, request: UserRegistrationRequest) -> UserProfile:
        m1_user = UserRepository.get_module1_user_by_id(db, user_id)
        if not m1_user:
            raise HTTPException( status_code=404, detail="User not found. Please register first.")

        if UserRepository.get_by_user_id(db, user_id):
            raise HTTPException( status_code=409, detail="KYC profile already exists for this user.")

        if UserRepository.get_by_email(db, request.email):
            raise HTTPException( status_code=409, detail="Email already registered.")

        if UserRepository.get_by_pan_number(db, request.pan_number):
            raise HTTPException( status_code=409, detail="PAN number already registered.")

        if UserRepository.get_by_aadhaar_number(db, request.aadhaar_number):
            raise HTTPException(status_code=409, detail="Aadhaar number already registered.")

        now = datetime.now(timezone.utc)

        new_profile = UserProfile(
            user_id=user_id,
            email=request.email,
            full_name=request.full_name,
            pan_number=request.pan_number,
            aadhaar_number=request.aadhaar_number,
            dob=request.dob,
            permanent_address=request.permanent_address,
            temporary_address=request.temporary_address,
            employment_type=request.employment_type,
            monthly_income=request.monthly_income,
            pan_status="PENDING",
            created_at=now,
            updated_at=now,
        )

        profile = UserRepository.create_user(db, new_profile)

        return profile

    # =====================================================
    # GET PROFILE
    # =====================================================
    @staticmethod
    def get_profile(db: Session, user_id: int):

        profile = UserRepository.get_by_user_id(db, user_id)

        if not profile:
            raise HTTPException( status_code=404, detail="KYC profile not found.")

        return profile

    # =====================================================
    # UPDATE PROFILE
    # =====================================================
    @staticmethod
    def update_profile( db: Session, user_id: int, update_data) -> dict:

        user = UserRepository.get_by_user_id(db, user_id)

        if not user:
            raise HTTPException( status_code=404, detail="KYC profile not found for this user.")

        updated_fields = []

        # -----------------------------
        # FULL NAME
        # -----------------------------
        if update_data.full_name is not None:
            if user.name_locked:
                raise HTTPException( status_code=403, detail="Name cannot be changed after PAN verification.")
            user.full_name = update_data.full_name
            updated_fields.append("full_name")

        # -----------------------------
        # PAN
        # -----------------------------
        if update_data.pan_number is not None:
            if user.pan_locked:
                raise HTTPException( status_code=403, detail="PAN cannot be changed after verification.")

            existing_pan = UserRepository.get_by_pan_number(db, update_data.pan_number)
            if existing_pan and existing_pan.user_id != user_id:
                raise HTTPException( status_code=409, detail="PAN number already in use.")

            user.pan_number = update_data.pan_number
            updated_fields.append("pan_number")

        # -----------------------------
        # AADHAAR
        # -----------------------------
        if update_data.aadhaar_number is not None:
            if user.aadhaar_locked:
                raise HTTPException( status_code=403, detail="Aadhaar cannot be changed after verification.")

            user.aadhaar_number = update_data.aadhaar_number
            updated_fields.append("aadhaar_number")

        # -----------------------------
        # DOB
        # -----------------------------
        if update_data.dob is not None:
            if user.dob_locked:
                raise HTTPException( status_code=403, detail="Date of birth cannot be changed after verification.")

            user.dob = update_data.dob
            updated_fields.append("dob")

        # -----------------------------
        # ADDRESS
        # -----------------------------
        if update_data.temporary_address is not None:
            user.temporary_address = update_data.temporary_address
            updated_fields.append("temporary_address")

        # -----------------------------
        # EMPLOYMENT
        # -----------------------------
        if update_data.employment_type is not None:
            user.employment_type = update_data.employment_type
            updated_fields.append("employment_type")

        # -----------------------------
        # INCOME
        # -----------------------------
        if update_data.monthly_income is not None:
            user.monthly_income = update_data.monthly_income
            updated_fields.append("monthly_income")

        if not updated_fields:
            raise HTTPException( status_code=400, detail="No fields provided for update.")

        user.updated_at = datetime.now(timezone.utc)

        UserRepository.update_user(db, user)

        return {
            "success": True,
            "message": "Profile updated successfully.",
            "data": {
                "user_id": user.user_id,
                "email": user.email,
                "updated_fields": updated_fields,
            },
        }