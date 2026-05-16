from fastapi import FastAPI
from contextlib import asynccontextmanager

# ------------------- CORE -------------------
from core.database import Base, engine, SessionLocal
from core.seed import create_default_super_admin
from core.config import settings
from consent.seed import seed_all
from utils.db_init import ensure_enum_values

# ------------------- AUTH -------------------
from routers.Auth import lender, superadmin_access, login_SL, user_register, twofactor, email,forgot_password,biometric,support
from routers.Auth.superadmin_support_dashboard import router as superadmin_support_router
# ------------------- PROFILE & KYC -------------------
from routers.Profile_KYC.profile_router import router as profile_router
from routers.Profile_KYC.pan_router import router as pan_router
from routers.Profile_KYC.aadhaar_router import router as aadhaar_router
from routers.Profile_KYC.bank_router import router as bank_router
from routers.Profile_KYC.document_router import router as document_router
from routers.Profile_KYC.admin_router import router as admin_router
from services.Profile_KYC.auto_cleanup import AutoCleanup
from routers.Profile_KYC.email_verify_router import router as email_verify_router


# ------------------- CONSENT -------------------
from routers.Consent.consent_routers import router as consent_router
from routers.Consent.legal_routers import router as legal_router

# ------------------- SETTINGS -------------------
from routers.Settings.profile_router import router as settings_profile_router
from routers.Settings.settings_router import router as settings_router

# ------------------- ELIGIBILITY -------------------
from routers.Eligibility.credit_route import router as credit_router
from routers.Eligibility.eligibility_route import router as eligibility_router
from routers.Eligibility.eligibility_result import router as eligibility_result_router
from routers.Eligibility.get_lenders import router as get_lenders_router
from routers.Eligibility.select_lender import router as select_lender_router
from routers.Eligibility.loan_calculator_route import router as loan_calculator_router

# ------------------- LOAN APPLICATION -------------------
from routers.Loan_application.loan_application_router import router as loan_application_router
from routers.Loan_application.loan_application_purpose_router import router as loan_application_purpose_router
from routers.Loan_application.loan_application_reference_router import router as loan_application_reference_router
from routers.Loan_application.reference_otp_router import router as reference_otp_router
from routers.Loan_application.loan_application_declaration_router import router as loan_application_declaration_router
from routers.Loan_application.loan_application_summary_router import router as loan_application_summary_router
from routers.Loan_application.lender_dashboard_router import router as lender_dashboard_router
from routers.Loan_application.razorpayx_webhook import router as razorpayx_webhook_router
from routers.Loan_application.user_predisbursement_router import router as user_predisbursement_router
from routers.Loan_application.loan_application_submit_router import router as loan_application_submit_router

# ------------------- TRACKING -------------------
from routers.Tracking.tracking_router import router as tracking_router
#from routers.Tracking.reupload_router import router as reupload_router
from routers.Tracking.document_status_router import router as reupload_router
from routers.Tracking.nbfc_webhook_router import router as nbfc_router
from routers.Tracking.notifications_router import router as notifications_router
from routers.Tracking.internal_status_router import router as internal_status_router

# ------------------- REPAYMENT -------------------
from routers.Repayment.generate_emi import router as generate_emi_router
from routers.Repayment.emi_pdf import router as emi_pdf_router
from routers.Repayment.emi_reminder import router as emi_reminder_router
from routers.Repayment.overdue import router as overdue_router
from routers.Repayment.auto_debit import router as auto_debit_router
from routers.Repayment.manual import router as manual_router
from routers.Repayment.prepay_route import router as prepay_route_router
from routers.Repayment.foreclosure import router as foreclosure_router
from routers.Repayment.payment_history import router as payment_history_router
from routers.Repayment.payment_receipt import router as payment_receipt_router
from routers.Repayment.loan_closure import router as loan_closure_router
from routers.Repayment.ndc import router as ndc_router
from routers.Repayment.webhook import router as razorpay_webhook_router
# ------------------- SUPPORT -------------------
from routers.Support.faq import router as faq_router
from routers.Support.chat import router as chat_router
from routers.Support.complaint import router as complaint_router
from routers.Support.contact import router as contact_router
from routers.Support.grievance import router as grievance_router
from routers.Support.support_dashboard import (
    router as support_dashboard_router)
from routers.Support.complaint_reply import router as complaint_reply_router
# ------------------- ESIGN -------------------
from routers.Esign.esign_router import router as esign_router
from routers.Esign.agreement_router import router as agreement_router



# ------------------- APP -------------------
app = FastAPI(title="Loan Service Platform - API")

Base.metadata.create_all(bind=engine, checkfirst=True)
auto_cleanup = AutoCleanup(interval_hours=24)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine, checkfirst=True)

    auto_cleanup.start()
    print("Auto cleanup service started")
    yield
    auto_cleanup.stop()
    print("Auto cleanup service stopped")

# ------------------- STARTUP -------------------
@app.on_event("startup")
async def startup():
    db = SessionLocal()
    try:
        # Create default super admin
        if settings.SUPER_ADMIN_MOBILE and settings.SUPER_ADMIN_PASSWORD:
            create_default_super_admin(
                db,
                settings.SUPER_ADMIN_NAME,
                settings.SUPER_ADMIN_MOBILE,
                settings.SUPER_ADMIN_PASSWORD,
                settings.SUPER_ADMIN_DEVICE_ID,
            )

        # Seed data
        seed_all(db)

    finally:
        db.close()


# ------------------- ROUTES -------------------
app.include_router(login_SL.router)
app.include_router(user_register.router)
app.include_router(lender.router)
app.include_router(superadmin_access.router)
app.include_router(twofactor.router)
app.include_router(email.router)
app.include_router(forgot_password.router)
app.include_router(biometric.router)
app.include_router(support.router)
app.include_router(superadmin_support_router)

app.include_router(profile_router)
app.include_router(email_verify_router)
app.include_router(pan_router)
app.include_router(aadhaar_router)
app.include_router(bank_router)
app.include_router(document_router)
app.include_router(admin_router)

app.include_router(consent_router)
app.include_router(legal_router)

app.include_router(credit_router, tags=["Credit Profile"])
app.include_router(eligibility_router, tags=["Loan Eligibility"])
app.include_router(eligibility_result_router, tags=["Loan Eligibility"])
app.include_router(get_lenders_router, tags=["Lenders"])
app.include_router(select_lender_router, tags=["Lenders"])
app.include_router(loan_calculator_router, tags=["Loan Calculator"])

app.include_router(loan_application_router)
app.include_router(loan_application_purpose_router)
app.include_router(loan_application_reference_router)
app.include_router(reference_otp_router)
app.include_router(loan_application_declaration_router)
app.include_router(loan_application_summary_router)
app.include_router(loan_application_submit_router)
app.include_router(user_predisbursement_router)
app.include_router(lender_dashboard_router)
app.include_router(razorpayx_webhook_router)

app.include_router(tracking_router)
app.include_router(reupload_router)
app.include_router(nbfc_router)
app.include_router(notifications_router)
app.include_router(internal_status_router)

app.include_router(generate_emi_router)
app.include_router(emi_pdf_router)
app.include_router(emi_reminder_router)
app.include_router(overdue_router)
app.include_router(auto_debit_router)
app.include_router(manual_router)
app.include_router(razorpay_webhook_router)
app.include_router(prepay_route_router)
app.include_router(foreclosure_router)
app.include_router(payment_history_router)
app.include_router(payment_receipt_router)
app.include_router(loan_closure_router)
app.include_router(ndc_router)

app.include_router(agreement_router)
app.include_router(esign_router)


app.include_router(faq_router)
app.include_router(chat_router)
app.include_router(complaint_router)
app.include_router(contact_router)
app.include_router(grievance_router)
app.include_router(
    support_dashboard_router)
app.include_router(complaint_reply_router)

app.include_router(settings_profile_router)
app.include_router(settings_router)


# ------------------- ROOT -------------------
@app.get("/")
def root():
    return {"message": "API is running successfully"}