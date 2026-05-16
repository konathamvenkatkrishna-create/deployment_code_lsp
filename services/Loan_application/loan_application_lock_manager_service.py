from datetime import datetime, timezone
from fastapi import HTTPException

from models.Loan_application.loan_application import LoanApplication


class ApplicationLockManager:

    # =====================================================
    # 🔒 LOCK APPLICATION AFTER SUBMISSION
    # =====================================================
    @staticmethod
    def lock_application(application: LoanApplication):

        # -------------------------------------------------
        # ❌ Do NOT allow locking before submission
        # -------------------------------------------------
        if not application.is_submitted:
            raise HTTPException(400, "Cannot lock application before submission")

        # -------------------------------------------------
        # ✅ Prevent double locking
        # -------------------------------------------------
        if getattr(application, "is_locked", False):
            return

        now = datetime.now(timezone.utc)

        # =====================================================
        # 🔒 Lock main application
        # =====================================================
        application.is_locked = True
        application.locked_at = now

        # =====================================================
        # 🔒 Lock declaration
        # =====================================================
        declaration = getattr(application, "declaration", None)
        if declaration:
            declaration.is_locked = True
            declaration.locked_at = now

        # =====================================================
        # 🔒 Lock references
        # =====================================================
        references = getattr(application, "references", [])
        if references:
            for ref in references:
                ref.is_locked = True
                ref.locked_at = now

        # =====================================================
        # 🔒 Lock purpose
        # =====================================================
        purpose = getattr(application, "purpose", None)
        if purpose:
            purpose.is_locked = True
            purpose.locked_at = now

    # =====================================================
    # ✏️ CHECK IF EDIT ALLOWED (USE IN ALL APIs)
    # =====================================================
    @staticmethod
    def ensure_editable(application: LoanApplication):

        # ❌ If submitted → no edits
        if application.is_submitted:
            raise HTTPException(400, "Application already submitted. Editing not allowed.")

        # ❌ If locked → no edits
        if getattr(application, "is_locked", False):
            raise HTTPException(400, "Application is locked.")

        return True