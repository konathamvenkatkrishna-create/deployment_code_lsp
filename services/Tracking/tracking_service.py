from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.logger import logger

from repositories.Tracking.loan_application_repo import LoanApplicationRepository
from repositories.Tracking.loan_status_history_repo import LoanStatusHistoryRepository

from models.Profile_KYC.user_profile import UserProfile


class TrackingService:

    # --------------------------------------------------
    # GET USER PROFILE
    # --------------------------------------------------
    @staticmethod
    def get_user_profile(db: Session, user_id: int):
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        if not profile:
            logger.error(f"[PROFILE NOT FOUND] user_id={user_id}")
            raise HTTPException(404, "User profile not found")

        return profile


    # --------------------------------------------------
    # GET LATEST APPLICATION
    # --------------------------------------------------
    @staticmethod
    def get_latest_application(db: Session, user_id: int):

        profile = TrackingService.get_user_profile(db, user_id)

        application = LoanApplicationRepository.get_latest_by_user(
            db,
            profile.user_id  # ✅ FIXED (correct mapping)
        )

        if not application:
            raise HTTPException(404, "No application found")

        return application


    # --------------------------------------------------
    # GET USER APPLICATIONS
    # --------------------------------------------------
    @staticmethod
    def get_user_applications(db: Session, user_id: int):

        profile = TrackingService.get_user_profile(db, user_id)

        apps = LoanApplicationRepository.get_user_applications(
            db,
            profile.user_id  # ✅ FIXED
        )

        response = []
        for app in apps:
            response.append({
                "application_id": app.id,
                "reference_number": app.reference_number,
                "approved_amount": str(app.approved_amount) if app.approved_amount else None,
                "interest_rate": str(app.interest_rate) if app.interest_rate else None,
                "requested_tenure_months": app.requested_tenure_months,
                "application_status": app.application_status.value if app.application_status else None,
                "current_step": app.current_step,
                "is_submitted": app.is_submitted
            })

        return response


    # --------------------------------------------------
    # GET APPLICATION STATUS (WITH ID)
    # --------------------------------------------------
    @staticmethod
    def get_application_status(db: Session, application_id: int, user_id: int):

        profile = TrackingService.get_user_profile(db, user_id)

        app = LoanApplicationRepository.get_by_id(db, application_id)

        # ✅ FIXED authorization
        if not app or app.user_profile_id != profile.user_id:
            raise HTTPException(404, "Application not found")

        return {
            "application_id": app.id,
            "reference_number": app.reference_number,
            "application_status": app.application_status.value,
            "is_submitted": app.is_submitted
        }


    # --------------------------------------------------
    # GET MY APPLICATION STATUS
    # --------------------------------------------------
    @staticmethod
    def get_my_application_status(db: Session, user_id: int):

        app = TrackingService.get_latest_application(db, user_id)

        return {
            "application_id": app.id,
            "reference_number": app.reference_number,
            "application_status": app.application_status.value,
            "is_submitted": app.is_submitted
        }


    # --------------------------------------------------
    # GET APPLICATION TIMELINE
    # --------------------------------------------------
    @staticmethod
    def get_application_timeline(db: Session, application_id: int, user_id: int):

        profile = TrackingService.get_user_profile(db, user_id)

        app = LoanApplicationRepository.get_by_id(db, application_id)

        # ✅ FIXED authorization
        if not app or app.user_profile_id != profile.user_id:
            raise HTTPException(404, "Loan application not found")

        history = LoanStatusHistoryRepository.get_timeline(db, application_id)

        return [
            {
                "id": item.id,
                "old_status": item.old_status.value if item.old_status else None,
                "new_status": item.new_status.value if item.new_status else None,
                "comment": item.comment,
                "created_at": item.created_at
            }
            for item in history
        ]


    # --------------------------------------------------
    # GET MY APPLICATION TIMELINE
    # --------------------------------------------------
    @staticmethod
    def get_my_application_timeline(db: Session, user_id: int):

        app = TrackingService.get_latest_application(db, user_id)

        history = LoanStatusHistoryRepository.get_timeline(db, app.id)

        return [
            {
                "id": item.id,
                "old_status": item.old_status.value if item.old_status else None,
                "new_status": item.new_status.value if item.new_status else None,
                "comment": item.comment,
                "created_at": item.created_at
            }
            for item in history
        ]