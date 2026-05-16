from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal

from models.Auth.lender import Lender
from models.Loan_application.loan_application import LoanApplication
from models.Profile_KYC.user_profile import UserProfile

from core.Loan_calculator import calculate_loan_summary


class PreDisbursementService:

    # =====================================================
    # VALIDATION
    # =====================================================
    @staticmethod
    def _validate_application(application: LoanApplication):

        if not application.approved_amount:
            raise HTTPException(400, "Approved amount missing")

        if not application.requested_tenure_months:
            raise HTTPException(400, "Tenure not found")

    # =====================================================
    # CALCULATION
    # =====================================================
    @staticmethod
    def _calculate(db: Session, application: LoanApplication):

        interest_rate = application.interest_rate

        if not interest_rate and application.lender_id:
            lender = db.query(Lender).filter(
                Lender.id == application.lender_id
            ).first()
            interest_rate = lender.interest_rate if lender else None

        if not interest_rate:
            raise HTTPException(400, "Interest rate not found")

        loan_calc = calculate_loan_summary(
            principal=Decimal(application.approved_amount),
            interest_rate=Decimal(interest_rate),
            tenure_months=application.requested_tenure_months,
            first_emi_date=date.today()
        )

        return loan_calc, Decimal(interest_rate)

    # =====================================================
    # BUILD RESPONSE
    # =====================================================
    @staticmethod
    def _build_response(db: Session, application: LoanApplication, store=False):

        loan_calc, interest_rate = PreDisbursementService._calculate(
            db, application
        )

        processing_fee = Decimal(loan_calc.get("processing_fee") or 0)
        gst_amount = Decimal(loan_calc.get("gst_amount") or 0)

        total_processing_charges = processing_fee + gst_amount

        approved_amount = Decimal(application.approved_amount)

        disbursed_amount = approved_amount - total_processing_charges

        if disbursed_amount < 0:
            disbursed_amount = Decimal(0)

        # ✅ STORE ONLY FOR LENDER
        if store:
            application.disbursed_amount = disbursed_amount
            db.commit()
            db.refresh(application)

        # lender name
        lender_name = application.lender_name
        if not lender_name and application.lender_id:
            lender = db.query(Lender).filter(
                Lender.id == application.lender_id
            ).first()
            lender_name = lender.company_name if lender else None

        return {
            "application_id": application.id,
            "lender_name": lender_name,

            "approved_amount": float(application.approved_amount),
            "tenure_months": application.requested_tenure_months,
            "interest_rate_percent": float(interest_rate),
            "emi_amount": loan_calc["emi"],
            "total_repayment": loan_calc["total_amount"],
            "total_interest": loan_calc["total_interest"],

            "processing_fee": float(processing_fee),
            "gst_amount": float(gst_amount),
            "total_processing_charges": float(total_processing_charges),

            "net_disbursement_amount": float(disbursed_amount),
            "disbursed_amount": float(disbursed_amount),

            "repayment_schedule": loan_calc["schedule"]
        }

    # =====================================================
    # 👤 USER → NO APPLICATION ID REQUIRED
    # =====================================================
    @staticmethod
    def get_preview_for_user(
        db: Session,
        user_id: int
    ):

        # ✅ Get latest application automatically
        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(404, "No application found for user")

        # Optional: ensure ownership (extra safety)
        profile = db.get(UserProfile, application.user_profile_id)
        if not profile or profile.user_id != user_id:
            raise HTTPException(403, "Not authorized")

        PreDisbursementService._validate_application(application)

        return PreDisbursementService._build_response(
            db,
            application,
            store=False
        )

    # =====================================================
    # 🏦 LENDER → APPLICATION ID REQUIRED
    # =====================================================
    @staticmethod
    def get_preview(
        db: Session,
        application_id: int
    ):

        application = db.get(LoanApplication, application_id)

        if not application:
            raise HTTPException(404, "Application not found")

        PreDisbursementService._validate_application(application)

        return PreDisbursementService._build_response(
            db,
            application,
            store=True
        )