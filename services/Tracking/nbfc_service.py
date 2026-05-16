from sqlalchemy.orm import Session
import json

from repositories.Tracking.webhook_event_repo import WebhookEventRepository
from repositories.Tracking.loan_application_repo import LoanApplicationRepository

from services.Tracking.status_update_service import StatusUpdateService

from core.enums import LoanApplicationStatus


class NBFCService:

    @staticmethod
    def process_webhook(db: Session, data: dict):

        event_id = data["event_id"]
        application_id = data["application_id"]
        new_status = data["status"]
        payload = data.get("payload", {})

        # -------------------------------
        # Duplicate Check
        # -------------------------------
        existing = WebhookEventRepository.exists(db, event_id)
        if existing:
            return {
                "success": True,
                "message": "Duplicate event ignored"
            }

        # -------------------------------
        # Create event (PENDING)
        # -------------------------------
        WebhookEventRepository.create(
            db,
            {
                "event_id": event_id,
                "application_id": application_id,
                "payload": json.dumps(payload),
                "status": "PENDING"
            }
        )

        try:
            app = LoanApplicationRepository.get_by_id(db, application_id)

            if not app:
                WebhookEventRepository.mark_failed(db, event_id)
                raise Exception("Loan application not found")

            user_id = app.user_profile_id

            # -------------------------------
            # Map NBFC status
            # -------------------------------
            mapped_status = NBFCService.map_nbfc_status(new_status)

            if not mapped_status:
                WebhookEventRepository.mark_failed(db, event_id)
                raise Exception(f"Invalid NBFC status: {new_status}")

            # -------------------------------
            # 🚨 RULE: NBFC only till APPROVED
            # -------------------------------
            if mapped_status not in [
                LoanApplicationStatus.UNDER_REVIEW,
                LoanApplicationStatus.VERIFICATION_PENDING,
                LoanApplicationStatus.CREDIT_CHECK,
                LoanApplicationStatus.LENDER_REVIEW,
                LoanApplicationStatus.APPROVED,
                LoanApplicationStatus.REJECTED
            ]:
                WebhookEventRepository.mark_failed(db, event_id)
                raise Exception("NBFC not allowed to update this status")

            # -------------------------------
            # Update Status (Module 6)
            # -------------------------------
            StatusUpdateService.update_status(
                db=db,
                application_id=application_id,
                user_id=user_id,
                new_status=mapped_status,
                source="NBFC_WEBHOOK",
                comment=f"NBFC event: {new_status}"
            )

            # -------------------------------
            # Mark success
            # -------------------------------
            WebhookEventRepository.mark_processed(db, event_id)

            return {
                "success": True,
                "message": "Webhook processed successfully"
            }

        except Exception as e:
            WebhookEventRepository.mark_failed(db, event_id)
            raise e

    @staticmethod
    def map_nbfc_status(nbfc_status: str):

        normalized_status = nbfc_status.strip().upper()

        mapping = {
            "UNDER_REVIEW": LoanApplicationStatus.UNDER_REVIEW,
            "VERIFICATION_PENDING": LoanApplicationStatus.VERIFICATION_PENDING,
            "CREDIT_CHECK": LoanApplicationStatus.CREDIT_CHECK,
            "LENDER_REVIEW": LoanApplicationStatus.LENDER_REVIEW,

            # ✅ Support both formats
            "APPROVED": LoanApplicationStatus.APPROVED,
            "LOAN_APPROVED": LoanApplicationStatus.APPROVED,

            "REJECTED": LoanApplicationStatus.REJECTED,
            "LOAN_REJECTED": LoanApplicationStatus.REJECTED,
        }

        return mapping.get(normalized_status)