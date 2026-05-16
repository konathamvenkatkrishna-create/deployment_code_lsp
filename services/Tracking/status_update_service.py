from sqlalchemy import func
from sqlalchemy.orm import Session

from core.logger import logger
from core.enums import LoanApplicationStatus

from repositories.Tracking.loan_application_repo import LoanApplicationRepository
from repositories.Tracking.loan_status_history_repo import LoanStatusHistoryRepository

from services.Tracking.kyc_service import DocumentStatusService as KYCService
from services.Tracking.notification_service import NotificationService

from utils.notification_messages import NotificationMessages
from utils.agreement_client import initiate_esign
from utils.emi_client import generate_emi


class StatusUpdateService:

    # =====================================================
    # VALIDATION
    # =====================================================
    @staticmethod
    def validate_transition(old_status, new_status):
        VALID_TRANSITIONS = {
            LoanApplicationStatus.SUBMITTED: [LoanApplicationStatus.UNDER_REVIEW],
            LoanApplicationStatus.UNDER_REVIEW: [
                LoanApplicationStatus.VERIFICATION_PENDING,
                LoanApplicationStatus.CREDIT_CHECK,
                LoanApplicationStatus.REJECTED
            ],
            LoanApplicationStatus.VERIFICATION_PENDING: [LoanApplicationStatus.UNDER_REVIEW],
            LoanApplicationStatus.CREDIT_CHECK: [
                LoanApplicationStatus.LENDER_REVIEW,
                LoanApplicationStatus.REJECTED,
                LoanApplicationStatus.VERIFICATION_PENDING
            ],
            LoanApplicationStatus.LENDER_REVIEW: [
                LoanApplicationStatus.APPROVED,
                LoanApplicationStatus.REJECTED
            ],
            LoanApplicationStatus.APPROVED: [LoanApplicationStatus.AGREEMENT_PENDING],
            LoanApplicationStatus.AGREEMENT_PENDING: [LoanApplicationStatus.DISBURSEMENT_INITIATED],
            LoanApplicationStatus.DISBURSEMENT_INITIATED: [LoanApplicationStatus.DISBURSED],
            LoanApplicationStatus.DISBURSED: [LoanApplicationStatus.ACTIVE],
            LoanApplicationStatus.ACTIVE: [LoanApplicationStatus.CLOSED]
        }

        return new_status in VALID_TRANSITIONS.get(old_status, [])

    # =====================================================
    # MAIN METHOD
    # =====================================================
    @staticmethod
    def update_status(
        db: Session,
        application_id: int,
        user_id: int,
        new_status: str,
        source="SYSTEM",
        comment=None,
        token: str = None
    ):

        try:
            app = LoanApplicationRepository.get_by_id(db, application_id)

            if not app:
                raise Exception("Application not found")

            old_status = LoanApplicationStatus(app.application_status)
            new_status = LoanApplicationStatus(new_status)

            # SAME STATUS
            if old_status == new_status:
                return app

            # KYC check
            if new_status == LoanApplicationStatus.CREDIT_CHECK:
                kyc_status = KYCService.fetch_user_kyc_status(db, user_id)
                if kyc_status != "COMPLETED":
                    new_status = LoanApplicationStatus.VERIFICATION_PENDING
                    comment = "KYC incomplete"

            # VALIDATE TRANSITION
            if not StatusUpdateService.validate_transition(old_status, new_status):
                raise Exception(f"Invalid transition: {old_status} → {new_status}")

            # UPDATE STATUS
            updated_app = LoanApplicationRepository.update_status(
                db,
                application_id,
                new_status
            )

            # HISTORY
            LoanStatusHistoryRepository.insert_history(
                db=db,
                application_id=application_id,
                old_status=old_status.value,
                new_status=new_status.value,
                source=source,
                comment=comment
            )

            # =====================================================
            # SIDE EFFECTS (SAFE)
            # =====================================================

            # AGREEMENT FLOW
            if new_status == LoanApplicationStatus.AGREEMENT_PENDING:
                try:
                    initiate_esign(application_id, user_id)
                except Exception as e:
                    logger.error(f"[ESIGN ERROR] {str(e)}")

            # DISBURSED FLOW
            if new_status == LoanApplicationStatus.DISBURSED:
                app.disbursed_at = func.now()

                NotificationService.send_custom_message(
                    db=db,
                    user_id=user_id,
                    application_id=application_id,
                    title="Loan Status Update",
                    message=NotificationMessages.LOAN_DISBURSED.value,
                    notif_type="STATUS_UPDATE"
                )

                # auto move to ACTIVE
                return StatusUpdateService.update_status(
                    db,
                    application_id,
                    user_id,
                    LoanApplicationStatus.ACTIVE,
                    source="SYSTEM",
                    comment="Auto ACTIVE"
                )

            # ACTIVE FLOW
            if new_status == LoanApplicationStatus.ACTIVE:
                try:
                    if token:
                        generate_emi(token)
                except Exception as e:
                    logger.error(f"[EMI ERROR] {str(e)}")

            # NOTIFICATION
            NotificationService.send_custom_message(
                db=db,
                user_id=user_id,
                application_id=application_id,
                title="Loan Status Update",
                message=NotificationMessages.NBFC_STATUS_UPDATE.value,
                notif_type="STATUS_UPDATE"
            )

            db.commit()

            return updated_app

        except Exception as e:
            db.rollback()
            logger.error(f"[STATUS UPDATE ERROR] {str(e)}")
            raise