from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_application_references import LoanApplicationReference
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker

from core.enums import LoanApplicationStep, enum_value

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


class LoanApplicationReferenceService:

    # =====================================================
    # SAVE REFERENCES
    # =====================================================
    @staticmethod
    def save_references_form(
        db: Session,
        user_id: int,
        ref1_name,
        ref1_mobile_number,
        ref1_relation_type,
        ref1_is_emergency_contact,
        ref2_name,
        ref2_mobile_number,
        ref2_relation_type,
        ref2_is_emergency_contact,
    ):

        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(404, "No active draft application found")

        LoanApplicationService.ensure_editable(application)

        tracker = get_or_create_tracker(db, application)

        if not tracker.purpose_completed:
            raise HTTPException(
                status_code=400,
                detail="Complete purpose step before adding references"
            )

        try:
            # 🧹 Remove old references
            db.query(LoanApplicationReference).filter(
                LoanApplicationReference.application_id == application.id
            ).delete()

            # ✅ Create new references
            new_refs = [
                LoanApplicationReference(
                    application_id=application.id,
                    name=ref1_name,
                    mobile_number=ref1_mobile_number,
                    relation_type=ref1_relation_type,
                    is_emergency_contact=ref1_is_emergency_contact,
                    is_verified=False
                ),
                LoanApplicationReference(
                    application_id=application.id,
                    name=ref2_name,
                    mobile_number=ref2_mobile_number,
                    relation_type=ref2_relation_type,
                    is_emergency_contact=ref2_is_emergency_contact,
                    is_verified=False
                )
            ]

            db.add_all(new_refs)

            tracker.references_completed = False
            tracker.current_step = enum_value(LoanApplicationStep.REFERENCES)
            application.current_step = enum_value(LoanApplicationStep.REFERENCES)

            db.commit()

            for ref in new_refs:
                db.refresh(ref)

            return {
                "application_id": application.id,
                "references": [
                    {
                        "id": ref.id,   # ✅ FIXED
                        "name": ref.name,
                        "mobile_number": ref.mobile_number,
                        "relation_type": ref.relation_type,
                        "is_emergency_contact": ref.is_emergency_contact,  # ✅ FIXED
                        "is_verified": ref.is_verified
                    }
                    for ref in new_refs
                ],
                "current_step": "REFERENCES",
                "next_step": "VERIFY_REFERENCES",
                "message": "References saved successfully. Please verify references."
            }

        except Exception:
            db.rollback()
            raise HTTPException(500, "Failed to save references")

    # =====================================================
    # GET REFERENCES
    # =====================================================
    @staticmethod
    def get_references(db: Session, user_id: int):

        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(404, "No application found")

        refs = db.query(LoanApplicationReference).filter(
            LoanApplicationReference.application_id == application.id
        ).all()

        return {
            "application_id": application.id,
            "references": [
                {
                    "id": ref.id,   # ✅ FIXED
                    "name": ref.name,
                    "mobile_number": ref.mobile_number,
                    "relation_type": ref.relation_type,
                    "is_emergency_contact": ref.is_emergency_contact,
                    "is_verified": ref.is_verified
                }
                for ref in refs
            ] if refs else [],
            "is_references_added": len(refs) > 0,
            "current_step": application.current_step
        }