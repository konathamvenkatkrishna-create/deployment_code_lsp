from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal

from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker
from models.Profile_KYC.user_profile import UserProfile
from models.Auth.user import User
from models.Auth.lender import Lender
from models.Loan_application.loan_application_declaration import LoanApplicationDeclaration

from core.Loan_calculator import calculate_loan_summary

from schemas.Loan_application.loan_application_summary import (
    UserSummarySchema,
    LoanDetailsSummarySchema,
    LoanPurposeSummarySchema,
    ReferenceSummarySchema,
    ReferencesStatusSchema,
    DeclarationSummarySchema,
    SubmissionStatusSchema,
    LoanApplicationSummaryResponseSchema,
)

from core.enums import LoanApplicationStep, enum_value


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
            current_step=enum_value(LoanApplicationStep.LOAN_DETAILS),
            last_completed_step=None
        )
        db.add(tracker)
        db.commit()
        db.refresh(tracker)

    return tracker


class LoanApplicationSummaryService:

    @staticmethod
    def get_summary_by_user(db: Session, user_id: int):

        # ================= USER PROFILE =================
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        if not profile:
            raise HTTPException(404, "User profile not found")

        # ================= APPLICATION =================
        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == profile.user_id
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(404, "No application found")

        tracker = get_or_create_tracker(db, application)

        # =====================================================
        # STEP VALIDATION (STRICT FLOW)
        # =====================================================
        if not tracker.loan_details_completed:
            raise HTTPException(400, {"pending_step": "LOAN_DETAILS"})

        if not tracker.purpose_completed:
            raise HTTPException(400, {"pending_step": "PURPOSE"})

        if not tracker.references_completed:
            raise HTTPException(400, {"pending_step": "REFERENCES"})

        if not tracker.declaration_completed:
            raise HTTPException(400, {"pending_step": "DECLARATION"})

        # =====================================================
        # SAFE PURPOSE CHECK
        # =====================================================
        if not application.purpose:
            raise HTTPException(400, {"pending_step": "PURPOSE"})

        # =====================================================
        # SAFE DECLARATION CHECK
        # =====================================================
        declaration_data = db.query(LoanApplicationDeclaration).filter(
            LoanApplicationDeclaration.application_id == application.id
        ).first()

        if not declaration_data:
            raise HTTPException(400, {"pending_step": "DECLARATION"})

        # =====================================================
        # LOAN VALIDATION
        # =====================================================
        if not application.requested_tenure_months:
            raise HTTPException(400, "Tenure not selected")

        if not application.lender_id:
            raise HTTPException(400, "Lender not selected")

        lender = db.query(Lender).filter(
            Lender.id == application.lender_id
        ).first()

        if not lender:
            raise HTTPException(404, "Lender not found")

        user = db.get(User, profile.user_id)

        if not user:
            raise HTTPException(404, "User not found")

        approved_amount = application.approved_amount or 0

        if not approved_amount:
            raise HTTPException(400, "Eligible amount not available")

        # =====================================================
        # CALCULATION
        # =====================================================
        loan_calc = calculate_loan_summary(
            principal=Decimal(approved_amount),
            interest_rate=Decimal(lender.interest_rate),
            tenure_months=application.requested_tenure_months,
            first_emi_date=date.today()
        )

        # =====================================================
        # USER SUMMARY
        # =====================================================
        user_summary = UserSummarySchema(
            user_id=user.id,
            full_name=profile.full_name or "",
            mobile_number=user.mobile_number,
            email=profile.email or ""
        )

        # =====================================================
        # LOAN DETAILS
        # =====================================================
        loan_details = LoanDetailsSummarySchema(
            approved_amount=approved_amount,
            requested_tenure_months=application.requested_tenure_months,
            interest_rate=lender.interest_rate,
            emi_amount=loan_calc["emi"],
            total_repayment=application.total_repayment,
            processing_fee=loan_calc["processing_fee"],
            gst_on_processing_fee=application.gst_amount,
            total_processing_charges=(application.processing_fee or 0) + (application.gst_amount or 0),
            lender_name=lender.company_name
        )

        # =====================================================
        # PURPOSE
        # =====================================================
        purpose = LoanPurposeSummarySchema(
            purpose=application.purpose.purpose_code
        )

        # =====================================================
        # REFERENCES
        # =====================================================
        reference_list = [
            ReferenceSummarySchema(
                name=ref.name,
                relationship=ref.relation_type,
                mobile_number=ref.mobile_number,
                is_mobile_verified=ref.is_verified
            )
            for ref in (application.references or [])
        ]

        verified_count = sum(ref.is_verified for ref in (application.references or []))

        reference_status = ReferencesStatusSchema(
            total_required=2,
            total_added=len(application.references or []),
            verified_count=verified_count,
            remaining_to_verify=max(0, 2 - verified_count)
        )

        # =====================================================
        # DECLARATION
        # =====================================================
        declaration = DeclarationSummarySchema(
            agreed_terms=declaration_data.agreed_terms,
            consent_credit_check=declaration_data.consent_credit_check,
            consent_timestamp=declaration_data.consent_timestamp,
            has_existing_loans=declaration_data.has_existing_loans,
            has_credit_card=declaration_data.has_credit_card,
            has_default_history=declaration_data.has_default_history,
            declaration_accepted=declaration_data.agreed_terms
        )

        # =====================================================
        # SUBMISSION STATUS
        # =====================================================
        submission_status = SubmissionStatusSchema(
            last_completed_step=tracker.last_completed_step,
            can_submit=True,
            pending_steps=[]
        )

        # =====================================================
        # FINAL STEP UPDATE
        # =====================================================
        tracker.current_step = enum_value(LoanApplicationStep.SUMMARY)
        application.current_step = enum_value(LoanApplicationStep.SUMMARY)

        db.commit()

        # =====================================================
        # RESPONSE
        # =====================================================
        return LoanApplicationSummaryResponseSchema(
            application_id=application.id,
            user=user_summary,
            loan_details=loan_details,
            purpose=purpose,
            references=reference_list,
            reference_status=reference_status,
            declaration=declaration,
            submission_status=submission_status
        )