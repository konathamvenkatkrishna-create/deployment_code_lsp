from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from models.Esign.agreements import Agreement
from models.Loan_application.loan_application import LoanApplication
from models.Profile_KYC.user_profile import UserProfile

from core.logger import logger
from core.exceptions import throw_error

from services.Esign.pdf_generator import PDFGenerator


class AgreementService:

    def __init__(self, pdf: PDFGenerator):
        self.pdf = pdf

    # =====================================================
    # 📄 GENERATE / FETCH AGREEMENT
    # =====================================================
    def fetch_agreement_for_user(self, user_id: int, db: Session):

        logger.info(f"[Agreement] Fetching for user_id={user_id}")

        try:
            # -------------------------------------------------
            # 🔍 GET USER PROFILE
            # -------------------------------------------------
            profile = db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()

            if not profile:
                throw_error("User profile not found", 404)

            user_profile_id = profile.user_id

            # -------------------------------------------------
            # 🔍 FETCH APPLICATION
            # -------------------------------------------------
            application = db.query(LoanApplication).filter(
                LoanApplication.user_profile_id == user_profile_id,
                LoanApplication.application_status.in_([
                    "APPROVED",
                    "AGREEMENT_GENERATED",
                    "ESIGN_COMPLETED"
                ])
            ).order_by(LoanApplication.id.desc()).with_for_update().first()

            if not application:
                throw_error(
                    "No eligible application found. Please complete approval first.",
                    404
                )

            application_id = application.id

            # -------------------------------------------------
            # 🔍 CHECK EXISTING AGREEMENT
            # -------------------------------------------------
            existing = db.query(Agreement).filter(
                Agreement.application_id == application_id,
                Agreement.is_active == True
            ).first()

            if existing:
                logger.info(f"[Agreement] Existing agreement found for app={application_id}")

                return {
                    "exists": True,
                    "loan_id": application_id,
                    "pdf_path": existing.agreement_pdf_path,
                    "status": existing.esign_status,
                    "signed_pdf_path": existing.signed_pdf_path,
                }

            # -------------------------------------------------
            # 🔢 VERSIONING
            # -------------------------------------------------
            latest = db.query(Agreement).filter(
                Agreement.application_id == application_id
            ).order_by(Agreement.version.desc()).first()

            new_version = 1 if not latest else latest.version + 1

            # -------------------------------------------------
            # 👤 BORROWER NAME (🔥 FIXED)
            # -------------------------------------------------
            borrower_name = (
                getattr(profile, "full_name", None)
                or f"{getattr(profile, 'first_name', '')} {getattr(profile, 'last_name', '')}".strip()
                or getattr(profile, "name", None)
            )

            if not borrower_name:
                borrower_name = f"User-{user_id}"

            # -------------------------------------------------
            # 💰 INTEREST RATE (🔥 FIXED)
            # -------------------------------------------------
            interest_rate = getattr(application, "interest_rate", None)
            interest_rate = round(float(interest_rate or 0), 2)

            # -------------------------------------------------
            # 📄 GENERATE PDF
            # -------------------------------------------------
            pdf_output = self.pdf.generate_agreement(
                application_id=application_id,
                borrower_name=borrower_name,
                loan_amount=application.approved_amount,
                interest_rate=interest_rate
            )

            file_path = pdf_output.get("file_path")

            if not file_path:
                throw_error("PDF generation failed", 500)

            file_hash = self.pdf.generate_hash(file_path)

            # -------------------------------------------------
            # ❗ DEACTIVATE OLD AGREEMENTS
            # -------------------------------------------------
            db.query(Agreement).filter(
                Agreement.application_id == application_id,
                Agreement.is_active == True
            ).update({"is_active": False})

            # -------------------------------------------------
            # 💾 SAVE AGREEMENT
            # -------------------------------------------------
            agreement = Agreement(
                application_id=application_id,
                user_id=user_id,
                version=new_version,
                agreement_pdf_path=file_path,
                file_hash=file_hash,
                is_active=True,
                esign_status="PENDING"
            )

            db.add(agreement)

            # -------------------------------------------------
            # 🔄 UPDATE APPLICATION STATUS
            # -------------------------------------------------
            application.application_status = "AGREEMENT_GENERATED"

            db.commit()
            db.refresh(agreement)

            logger.info(f"[Agreement] Generated successfully for app={application_id}")

            return {
                "exists": False,
                "loan_id": application_id,
                "pdf_path": file_path,
                "status": agreement.esign_status,
                "signed_pdf_path": None
            }

        except SQLAlchemyError as db_err:
            db.rollback()
            logger.error(f"[Agreement][DB ERROR]: {str(db_err)}")
            throw_error("Database error while generating agreement", 500)

        except Exception as e:
            db.rollback()
            logger.error(f"[Agreement][ERROR]: {str(e)}")
            throw_error("Agreement generation failed", 500)

    # =====================================================
    # 📄 GET EXISTING AGREEMENT
    # =====================================================
    def get_existing_agreement(self, user_id: int, db: Session):

        logger.info(f"[Agreement] Fetch existing agreement user_id={user_id}")

        try:
            profile = db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()

            if not profile:
                return None

            user_profile_id = profile.user_id

            application = db.query(LoanApplication).filter(
                LoanApplication.user_profile_id == user_profile_id,
                LoanApplication.application_status.in_([
                    "APPROVED",
                    "AGREEMENT_GENERATED",
                    "ESIGN_COMPLETED"
                ])
            ).order_by(LoanApplication.id.desc()).first()

            if not application:
                return None

            agreement = db.query(Agreement).filter(
                Agreement.application_id == application.id,
                Agreement.is_active == True
            ).first()

            return agreement

        except Exception as e:
            logger.error(f"[Agreement GET ERROR]: {str(e)}")
            return None