from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.Esign.esign_session import EsignSession, EsignStatus
from models.Esign.signed_documents import SignedDocument
from models.Esign.agreements import Agreement
from models.Loan_application.loan_application import LoanApplication
from models.Profile_KYC.user_profile import UserProfile

from providers.factory import get_esign_provider

from core.exceptions import throw_error
from core.logger import logger
from core.enums import PaymentModeEnum

from utils.file_handler import FileHandler


class EsignService:

    def __init__(self):
        self.file_handler = FileHandler()

    # =====================================================
    # 🔐 INITIATE E-SIGN (🔥 FIXED WITH RETRY)
    # =====================================================
    async def initiate_esign(self, db: Session, user_id: int):

        logger.info(f"[E-SIGN INIT] user_id={user_id}")

        loan = db.query(LoanApplication).join(UserProfile).filter(
            UserProfile.user_id == user_id,
            LoanApplication.application_status.in_(["APPROVED", "AGREEMENT_GENERATED"])
        ).order_by(LoanApplication.id.desc()).first()

        if not loan:
            throw_error("No valid loan found for eSign", 404)

        if not loan.user_profile or not getattr(loan.user_profile, "aadhaar_number", None):
            throw_error("Aadhaar not available", 400)

        aadhaar_number = loan.user_profile.aadhaar_number

        # 🔥 FIX: Allow retry (delete old session if exists)
        existing = db.query(EsignSession).filter(
            EsignSession.application_id == loan.id,
            EsignSession.status == EsignStatus.OTP_SENT
        ).first()

        if existing:
            logger.warning(f"[ESIGN RETRY] deleting old session txn={existing.transaction_id}")
            db.delete(existing)
            db.commit()

        agreement_id = self._get_active_agreement_id(db, loan.id)

        provider = get_esign_provider()

        payload = {
            "loan_id": loan.id,
            "aadhaar_number": aadhaar_number
        }

        try:
            provider_resp = await provider.initiate_esign(payload)
        except Exception as exc:
            logger.error(f"[E-SIGN INIT ERROR]: {str(exc)}")
            throw_error("eSign provider unreachable", 503)

        txn = provider_resp.get("transaction_id") or provider_resp.get("txn_id")

        if not txn:
            throw_error("Invalid provider response", 502)

        try:
            session = EsignSession(
                application_id=loan.id,
                agreement_id=agreement_id,
                user_id=user_id,
                transaction_id=txn,
                request_payload=payload,
                response_payload=provider_resp,
                status=EsignStatus.OTP_SENT
            )

            db.add(session)
            db.commit()

        except IntegrityError:
            db.rollback()
            throw_error("Duplicate transaction", 409)

        return {
            "transaction_id": txn,
            "masked_aadhaar": provider_resp.get("masked_aadhaar")
        }

    # =====================================================
    # 🔐 VERIFY OTP
    # =====================================================
    async def verify_esign(self, data, db: Session):

        session = db.query(EsignSession).filter(
            EsignSession.transaction_id == data.transaction_id
        ).with_for_update().first()

        if not session:
            throw_error("Invalid transaction ID", 404)

        if session.status == EsignStatus.SIGNED:
            return {"status": "SIGNED"}

        existing_signed = db.query(EsignSession).filter(
            EsignSession.agreement_id == session.agreement_id,
            EsignSession.status == EsignStatus.SIGNED
        ).with_for_update().first()

        if existing_signed:
            return {"status": "SIGNED", "message": "Already signed"}

        provider = get_esign_provider()

        try:
            provider_resp = await provider.verify_esign(data.model_dump())
        except Exception as exc:
            logger.error(f"[VERIFY ERROR]: {str(exc)}")
            throw_error("OTP verification failed", 503)

        if provider_resp.get("status") != "SIGNED":
            throw_error("Invalid OTP", 400)

        session.status = EsignStatus.SIGNED

        # 🔥 Update agreement
        agreement = db.query(Agreement).filter(
            Agreement.id == session.agreement_id
        ).with_for_update().first()

        if agreement:
            agreement.esign_status = "SIGNED"

        # 🔥 Update loan
        loan = db.query(LoanApplication).filter(
            LoanApplication.id == session.application_id
        ).with_for_update().first()

        if loan:
            loan.application_status = "ESIGN_COMPLETED"

        db.commit()

        return {"status": "SIGNED"}

    # =====================================================
    # 🔥 CALLBACK HANDLER
    # =====================================================
    async def handle_callback(self, data, db: Session):

        logger.info(f"[CALLBACK] txn={data.transaction_id}")

        loan = None

        try:
            session = db.query(EsignSession).filter(
                EsignSession.transaction_id == data.transaction_id
            ).with_for_update().first()

            if not session:
                throw_error("Unknown transaction ID", 404)

            if session.status == EsignStatus.SIGNED:
                return {"status": "already_processed"}

            if data.status != "SIGNED":
                session.status = EsignStatus.FAILED
                db.commit()
                throw_error("Signing failed", 400)

            if not data.signed_pdf_url:
                throw_error("Signed PDF URL missing", 400)

            file_path, file_hash = await self.file_handler.download_and_save_pdf_async(
                url=data.signed_pdf_url,
                txn=session.transaction_id
            )

            db.add(SignedDocument(
                session_id=session.id,
                agreement_id=session.agreement_id,
                application_id=session.application_id,
                signed_pdf_path=file_path,
                file_hash=file_hash
            ))

            session.status = EsignStatus.SIGNED
            session.callback_payload = data.model_dump()

            # 🔥 Update agreement
            agreement = db.query(Agreement).filter(
                Agreement.application_id == session.application_id,
                Agreement.is_active == True
            ).with_for_update().first()

            if agreement:
                agreement.esign_status = "SIGNED"
                agreement.signed_pdf_path = file_path
                agreement.file_hash = file_hash

            # 🔥 Update loan
            loan = db.query(LoanApplication).filter(
                LoanApplication.id == session.application_id
            ).with_for_update().first()

            if loan:
                loan.application_status = "ESIGN_COMPLETED"

            db.commit()

        except Exception as e:
            db.rollback()
            logger.error(f"[CALLBACK ERROR] {str(e)}")
            throw_error("Callback processing failed", 500)

        # 🚀 DISBURSEMENT (SAFE)
        try:
            if loan and loan.application_status == "ESIGN_COMPLETED":
                from services.Loan_application.loan_disbursement_service import LoanDisbursementService

                LoanDisbursementService.disburse_loan(
                    db,
                    loan.id,
                    PaymentModeEnum.BANK
                )
        except Exception as e:
            logger.error(f"[DISBURSE ERROR] {str(e)}")

        return {
            "status": "success",
            "application_id": session.application_id,
            "file_path": file_path
        }

    # =====================================================
    # 🔧 HELPER
    # =====================================================
    def _get_active_agreement_id(self, db: Session, application_id: int):

        agreement = db.query(Agreement).filter(
            Agreement.application_id == application_id,
            Agreement.is_active == True
        ).first()

        if not agreement:
            throw_error("Active agreement not found", 404)

        return agreement.id