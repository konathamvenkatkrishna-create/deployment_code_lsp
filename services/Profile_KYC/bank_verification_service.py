from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.Profile_KYC.attempt_tracker import VerificationType
from models.Profile_KYC.user_profile import UserProfile
from repositories.Profile_KYC.user_repository import UserRepository
from repositories.Profile_KYC.attempt_tracker_repository import AttemptTrackerRepository
from repositories.Profile_KYC.kyc_bank_verification_repository import KYCBankVerificationRepository
from utils.name_matcher import name_match_percentage
from utils.razorpay_bank_client import create_contact, create_fund_account, validate_fund_account
from core.config import settings

class BankVerificationService:

    # ============================================================
    # SAVE BANK DETAILS
    # ============================================================
    @staticmethod
    def save_bank_details(
        db: Session,
        user: UserProfile,
        account_number: str,
        account_holder_name: str,
        bank_name: str,
        ifsc: str,
    ):
        if user.bank_locked or user.bank_status == "VERIFIED":
            raise HTTPException(400, "Bank account already verified")

        existing = KYCBankVerificationRepository.get_verified_by_account_number(
            db, account_number
        )
        if existing and existing.user_id != user.user_id:
            raise HTTPException(409, "Bank already linked to another user")

        return KYCBankVerificationRepository.create_verification_log(
            db=db,
            user_id=user.user_id,
            account_number=account_number,
            account_holder_name=account_holder_name,
            bank_name=bank_name,
            ifsc=ifsc,
            name_match_percentage=0.0,
            status="PENDING",
            failure_reason=None,
            attempt_number=0,
        )

    # ============================================================
    # UPDATE BANK DETAILS
    # ============================================================
    @staticmethod
    def update_bank_details(
        db: Session,
        user: UserProfile,
        account_number: str | None,
        account_holder_name: str | None,
        bank_name: str | None,
        ifsc: str | None,
    ):
        if user.bank_locked or user.bank_status == "VERIFIED":
            raise HTTPException(403, "Cannot update verified bank")

        latest = KYCBankVerificationRepository.get_latest_by_user_id(db, user.user_id)
        if not latest:
            raise HTTPException(404, "No bank details found")

        final_account = account_number      or latest.account_number
        final_name    = account_holder_name or latest.account_holder_name
        final_bank    = bank_name           or latest.bank_name
        final_ifsc    = ifsc                or latest.ifsc

        return KYCBankVerificationRepository.create_verification_log(
            db=db,
            user_id=user.user_id,
            account_number=final_account,
            account_holder_name=final_name,
            bank_name=final_bank,
            ifsc=final_ifsc,
            name_match_percentage=0.0,
            status="PENDING",
            failure_reason=None,
            attempt_number=0,
        )

    # ============================================================
    # VERIFY BANK ACCOUNT  — Razorpay X penny drop
    # ============================================================
    @staticmethod
    def verify_bank_account(
        db: Session,
        user: UserProfile,
        account_number: str,
        account_holder_name: str,
        bank_name: str,
        ifsc: str,
    ):
        if user.bank_status == "VERIFIED":
            raise HTTPException(400, "Bank already verified")

        # ── Attempt Tracker ──────────────────────────────────────
        tracker = AttemptTrackerRepository.get_by_email_and_type(
            db, user.email, VerificationType.BANK
        )
        if not tracker:
            tracker = AttemptTrackerRepository.create_tracker(
                db, user.email, VerificationType.BANK
            )
            db.commit()

        now = datetime.now(timezone.utc)

        if tracker.locked_until and tracker.locked_until > now:
            raise HTTPException(
                423,
                f"Bank verification blocked. Try after {settings.BANK_COOLDOWN_HOURS} hours.",
            )
        if tracker.locked_until and tracker.locked_until <= now:
            AttemptTrackerRepository.reset_attempts(db, tracker)

        current_attempt = AttemptTrackerRepository.increment_attempt(db, tracker)

        # ── Razorpay X — 3 step penny drop ───────────────────────
        failure_reason = None
        match_pct      = 0.0

        try:
            latest = KYCBankVerificationRepository.get_latest_by_user_id(db, user.user_id)

            # Step 1 — Contact (create once, reuse on retry)
            if not latest.razorpay_contact_id:
                latest.razorpay_contact_id = create_contact(
                    name    = account_holder_name,
                    email   = user.email,
                    contact = getattr(user, "mobile", "+910000000000"),
                )
                db.commit()

            # Step 2 — Fund Account (create once, reuse on retry)
            if not latest.razorpay_fund_account_id:
                latest.razorpay_fund_account_id = create_fund_account(
                    contact_id     = latest.razorpay_contact_id,
                    name           = account_holder_name,
                    account_number = account_number,
                    ifsc           = ifsc,
                )
                db.commit()

            # Step 3 — Validate (penny drop)
            # Pass account_holder_name so test mode can use it for name match
            result = validate_fund_account(
                fund_account_id     = latest.razorpay_fund_account_id,
                account_holder_name = account_holder_name,
            )

            # Save validation ID
            if result.get("validation_id"):
                latest.razorpay_validation_id = result["validation_id"]
                db.commit()

            # Evaluate result
            if result["razorpay_status"] != "completed":
                failure_reason = "Bank validation could not be completed. Please try again."

            elif result["account_status"] != "active":
                failure_reason = "Bank account is inactive or invalid."

            else:
                # Name match against Razorpay's registered name
                # In test mode: registered_name == account_holder_name → always 100% match
                # In live mode: registered_name == actual bank name
                match_pct = name_match_percentage(
                    account_holder_name,
                    result.get("registered_name", ""),
                )
                if match_pct < settings.NAME_MATCH_THRESHOLD:
                    failure_reason = "Account holder name does not match bank records."

        except HTTPException as e:
            # Razorpay API / network error — treat as verification failure
            failure_reason = e.detail

        # ── Handle Failure ───────────────────────────────────────
        if failure_reason:
            if current_attempt >= settings.BANK_MAX_ATTEMPTS:
                user.bank_status = "BLOCKED"
                AttemptTrackerRepository.lock_tracker(
                    db,
                    tracker,
                    now + timedelta(hours=settings.BANK_COOLDOWN_HOURS),
                )
                status = "BLOCKED"
            else:
                user.bank_status = "FAILED"
                status = "FAILED"

            KYCBankVerificationRepository.create_verification_log(
                db=db,
                user_id=user.user_id,
                account_number=account_number,
                account_holder_name=account_holder_name,
                bank_name=bank_name,
                ifsc=ifsc,
                name_match_percentage=match_pct,
                status=status,
                failure_reason=failure_reason,
                attempt_number=current_attempt,
            )
            UserRepository.save(db)

            remaining = settings.BANK_MAX_ATTEMPTS - current_attempt
            if remaining > 0:
                raise HTTPException(
                    400,
                    f"{failure_reason} {remaining} attempt(s) remaining.",
                )
            raise HTTPException(
                423,
                f"{failure_reason} Maximum attempts reached. "
                f"Blocked for {settings.BANK_COOLDOWN_HOURS} hours.",
            )

        # ── Success ──────────────────────────────────────────────
        user.bank_status      = "VERIFIED"
        user.bank_locked      = True
        user.bank_verified_at = now

        KYCBankVerificationRepository.create_verification_log(
            db=db,
            user_id=user.user_id,
            account_number=account_number,
            account_holder_name=account_holder_name,
            bank_name=bank_name,
            ifsc=ifsc,
            name_match_percentage=match_pct,
            status="VERIFIED",
            failure_reason=None,
            attempt_number=current_attempt,
        )

        AttemptTrackerRepository.reset_attempts(db, tracker)
        UserRepository.update_user(db, user)

        return {
            "bank_status": "VERIFIED",
            "message":     "Bank account verified successfully",
        }