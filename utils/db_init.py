# utils/db_init.py

from sqlalchemy import text


def ensure_enum_values(db):
    values = [
        "SUBMITTED",
        "UNDER_REVIEW",
        "VERIFICATION_PENDING",
        "CREDIT_CHECK",
        "LENDER_REVIEW",
        "APPROVED",
        "REJECTED",
        "AGREEMENT_PENDING",
        "DISBURSEMENT_INITIATED",
        "DISBURSED",
        "ACTIVE",
        "CLOSED"
    ]

    for val in values:
        try:
            db.execute(
                text(f"ALTER TYPE loan_application_status_enum ADD VALUE IF NOT EXISTS '{val}'")
            )
            db.commit()
        except Exception:
            db.rollback()