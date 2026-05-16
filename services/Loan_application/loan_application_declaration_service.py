from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker
from models.Profile_KYC.user_profile import UserProfile
from models.Loan_application.loan_application_declaration import LoanApplicationDeclaration

from core.enums import LoanApplicationStep, LoanApplicationStatus, enum_value

from schemas.Loan_application.loan_application_declaration import (
    LoanApplicationDeclarationResponse
)

from services.Loan_application.loan_application_service import (
    LoanApplicationService,
)


# =====================================================
# HELPER
# =====================================================
def get_or_create_tracker(db: Session, application: LoanApplication):
    tracker = db.query(LoanApplicationStepTracker).filter(
        LoanApplicationStepTracker.application_id == application.id
    ).first()

    if not tracker:
        tracker = LoanApplicationStepTracker(
            application_id=application.id,
            loan_details_completed=False,
            purpose_completed=False,
            references_completed=False,
            declaration_completed=False,
            current_step=enum_value(LoanApplicationStep.EMI_CALCULATED),
            last_completed_step=None
        )
        db.add(tracker)
        db.commit()
        db.refresh(tracker)

    return tracker


class LoanApplicationDeclarationService:

    @staticmethod
    def save_declaration(
        db: Session,
        user_id: int,
        payload,
        ip_address: str,
        user_agent: str,
    ):

        # =====================================================
        # 1️⃣ Get User Profile
        # =====================================================
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        if not profile:
            raise HTTPException(404, "User profile not found")

        # =====================================================
        # 2️⃣ Get latest draft application
        # =====================================================
        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == profile.user_id,
            LoanApplication.is_submitted == False,
            LoanApplication.application_status == enum_value(LoanApplicationStatus.DRAFT)
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active draft application found"
            )

        # 🔐 Ensure editable
        LoanApplicationService.ensure_editable(application)

        # =====================================================
        # 3️⃣ Tracker
        # =====================================================
        tracker = get_or_create_tracker(db, application)

        # =====================================================
        # 4️⃣ Validation
        # =====================================================
        if not tracker.references_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"pending_step": "REFERENCES"}
            )

        if not payload.agreed_terms:
            raise HTTPException(400, "You must agree to Terms & Conditions")

        if not payload.consent_credit_check:
            raise HTTPException(400, "Credit bureau consent is mandatory")

        if not payload.consent_data_sharing:
            raise HTTPException(400, "Data sharing consent is mandatory")

        # =====================================================
        # 5️⃣ Save Declaration
        # =====================================================
        declaration = db.query(LoanApplicationDeclaration).filter(
            LoanApplicationDeclaration.application_id == application.id
        ).first()

        if not declaration:
            declaration = LoanApplicationDeclaration(
                application_id=application.id
            )
            db.add(declaration)

        declaration.has_existing_loans = payload.has_existing_loans
        declaration.has_credit_card = payload.has_credit_card
        declaration.has_default_history = payload.has_default_history

        declaration.agreed_terms = payload.agreed_terms
        declaration.consent_credit_check = payload.consent_credit_check
        declaration.consent_data_sharing = payload.consent_data_sharing

        declaration.terms_version = payload.terms_version
        declaration.privacy_policy_version = payload.privacy_policy_version

        declaration.consent_timestamp = datetime.now(timezone.utc)
        declaration.ip_address = ip_address
        declaration.user_agent = user_agent

        # =====================================================
        # 6️⃣ 🔥 STEP UPDATE (FINAL FIX)
        # =====================================================
        tracker.declaration_completed = True
        tracker.last_completed_step = enum_value(LoanApplicationStep.DECLARATION)

        # ✅ MOVE TO SUMMARY (CRITICAL FIX)
        tracker.current_step = enum_value(LoanApplicationStep.SUMMARY)
        application.current_step = enum_value(LoanApplicationStep.SUMMARY)

        db.add(tracker)
        db.add(application)
        db.commit()
        db.refresh(application)

        # =====================================================
        # 7️⃣ RESPONSE
        # =====================================================
        return {
            "application_id": application.id,
            "current_step": "SUMMARY",
            "next_step": "SUBMIT",
            "data": LoanApplicationDeclarationResponse(
                has_existing_loans=declaration.has_existing_loans,
                has_credit_card=declaration.has_credit_card,
                has_default_history=declaration.has_default_history,
                agreed_terms=declaration.agreed_terms,
                consent_credit_check=declaration.consent_credit_check,
                consent_timestamp=declaration.consent_timestamp,
                ip_address=declaration.ip_address,
                user_agent=declaration.user_agent,
            ),
            "message": "Declaration saved successfully"
        }