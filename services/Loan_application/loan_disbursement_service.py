from fastapi import HTTPException, BackgroundTasks
import requests

from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_transaction import LoanTransaction
from models.Esign.agreements import Agreement

from services.payment.razorpay_service import RazorpayService

from repositories.Loan_application.loan_disbursement_repo import LoanDisbursementRepository
from repositories.Loan_application.loan_transaction_repo import LoanTransactionRepository

from core.enums import (
    LoanApplicationStatus,
    DisbursementStatusEnum,
    PaymentModeEnum
)
from core.config import settings
from core.email_service import EmailService
from core.logger import logger


def match_payment_method(b, payment_mode):
    if getattr(b, "status", None) != "VERIFIED":
        return False

    if payment_mode.value == "BANK":
        return bool(getattr(b, "account_number", None))

    if payment_mode.value == "UPI":
        return bool(getattr(b, "upi_id", None))

    return False


class LoanDisbursementService:

    @staticmethod
    def disburse_loan(
        db: Session,
        application_id: int,
        payment_mode: PaymentModeEnum,
        background_tasks: BackgroundTasks | None = None
    ):

        try:
            # =====================================================
            # 🔒 LOCK APPLICATION
            # =====================================================
            application = (
                db.query(LoanApplication)
                .filter(LoanApplication.id == application_id)
                .with_for_update()
                .first()
            )

            if not application:
                raise HTTPException(404, "Application not found")

            # =====================================================
            # 📌 VALIDATION
            # =====================================================
            if application.application_status != LoanApplicationStatus.ESIGN_COMPLETED:
                raise HTTPException(
                    400,
                    f"Loan not ready for disbursement. Current status: {application.application_status}"
                )

            # =====================================================
            # 👤 USER PROFILE
            # =====================================================
            profile = application.user_profile

            if not profile:
                raise HTTPException(404, "User profile not found")

            user = profile.user

            # =====================================================
            # 🏦 VERIFIED PAYMENT METHOD
            # =====================================================
            payout_method = next(
                (
                    b for b in profile.bank_verifications
                    if match_payment_method(b, payment_mode)
                ),
                None
            )

            if not payout_method:
                raise HTTPException(400, "No verified payout method")

            # =====================================================
            # 🔁 EXISTING DISBURSEMENT CHECK
            # =====================================================
            existing = LoanDisbursementRepository.get_by_application_id(
                db,
                application.id
            )

            if existing and existing.payment_status == DisbursementStatusEnum.SUCCESS:
                raise HTTPException(400, "Loan already disbursed")

            # =====================================================
            # 📄 AGREEMENT VALIDATION
            # =====================================================
            agreement = (
                db.query(Agreement)
                .filter(
                    Agreement.application_id == application.id,
                    Agreement.is_active == True
                )
                .first()
            )

            if not agreement or agreement.esign_status != "SIGNED":
                raise HTTPException(400, "Agreement not signed")

            if not application.disbursed_amount:
                raise HTTPException(400, "Disbursement amount not available")

            net_amount = float(application.disbursed_amount)

            # =====================================================
            # 💸 PAYOUT
            # =====================================================
            if getattr(settings, "USE_MOCK_PAYOUT", False):

                logger.info("[MOCK PAYOUT] Using test mode")

                payout = {
                    "success": True,
                    "payout_id": f"mock_{application.id}_{int(datetime.utcnow().timestamp())}",
                    "status": "processing"
                }

            else:

                razorpay = RazorpayService()

                payout = razorpay.process_payout(
                    name=profile.full_name,
                    account_number=payout_method.account_number,
                    ifsc=payout_method.ifsc,
                    amount=net_amount,
                    email=profile.email,
                    phone=user.mobile_number
                )

            # =====================================================
            # ❌ PAYOUT FAILURE
            # =====================================================
            if not payout.get("success"):
                raise HTTPException(
                    500,
                    payout.get("error", "Payout failed")
                )

            payout_id = payout.get("payout_id")

            # =====================================================
            # 💾 SAVE DISBURSEMENT
            # =====================================================
            disbursement = LoanDisbursementRepository.upsert(
                db,
                application_id=application.id,
                data={
                    "amount": Decimal(net_amount),
                    "payment_mode": payment_mode,
                    "payment_status": DisbursementStatusEnum.PROCESSING,
                    "payment_reference_id": payout_id
                }
            )

            # =====================================================
            # 💾 SAVE TRANSACTION
            # =====================================================
            transaction = LoanTransaction(
                application_id=application.id,
                disbursement_id=disbursement.id,
                transaction_type="DISBURSEMENT",
                amount=Decimal(net_amount),
                status="PROCESSING",
                payment_mode=payment_mode.value,
                remarks="Disbursement initiated"
            )

            LoanTransactionRepository.create(db, transaction)

            # =====================================================
            # 🔄 UPDATE LOAN APPLICATION
            # =====================================================
            application.application_status = (
                LoanApplicationStatus.DISBURSEMENT_INITIATED
            )

            application.payout_status = (
                DisbursementStatusEnum.PROCESSING
            )

            application.current_step = "DISBURSEMENT_INITIATED"

            application.disbursed_at = datetime.utcnow()
            application.updated_at = datetime.utcnow()

            db.add(application)

            # =====================================================
            # 💾 COMMIT
            # =====================================================
            db.commit()

            # refresh latest state
            db.refresh(application)
            db.refresh(disbursement)

            logger.info(
                f"[DISBURSEMENT INITIATED] "
                f"application={application.id}, payout_id={payout_id}"
            )

        except Exception as e:
            db.rollback()

            logger.error(f"[DISBURSE ERROR] {str(e)}")

            raise

        # =====================================================
        # 📧 EMAIL
        # =====================================================
        try:

            email_body = f"""
            Dear {profile.full_name},

            Your loan disbursement has been initiated successfully.

            Amount: ₹{net_amount}
            Application ID: {application.id}

            Current Status: PROCESSING

            Thank you.
            """

            if background_tasks:

                background_tasks.add_task(
                    EmailService.send_email,
                    profile.email,
                    "Loan Disbursement Initiated",
                    email_body
                )

            else:

                EmailService.send_email(
                    profile.email,
                    "Loan Disbursement Initiated",
                    email_body
                )

            logger.info(f"[EMAIL SENT] {profile.email}")

        except Exception as e:

            logger.error(f"[EMAIL ERROR] {str(e)}")

        # =====================================================
        # 🔄 TRACKING
        # =====================================================
        try:

            if getattr(settings, "TRACKING_URL", None):

                requests.post(
                    settings.TRACKING_URL,
                    json={
                        "application_id": application.id,
                        "status": "DISBURSEMENT_INITIATED"
                    },
                    timeout=5
                )

        except Exception as e:

            logger.error(f"[TRACKING ERROR] {str(e)}")

        # =====================================================
        # ✅ RESPONSE
        # =====================================================
        return {
            "application_id": application.id,
            "payout_id": payout_id,
            "payout_status": application.payout_status,
            "application_status": application.application_status,
            "current_step": application.current_step,
            "message": "Disbursement initiated successfully"
        }