from math import pow
from sqlalchemy.orm import Session

from models.Eligibility.loan_calculation import LoanCalculation
from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker

from repositories.Eligibility.loan_calculator_repo import LoanCalculationRepository

from core.enums import LoanApplicationStep


MIN_LOAN_AMOUNT      = 5_000
MAX_LOAN_AMOUNT      = 20_000
ALLOWED_TENURES      = [3, 6, 9, 12]
ANNUAL_INTEREST_RATE = 12.0


class LoanCalculationService:

    # =====================================================
    # STEP UPDATE (🔥 CRITICAL FIX)
    # =====================================================
    @staticmethod
    def _update_emi_step(db: Session, user_id: int):

        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            return

        tracker = db.query(LoanApplicationStepTracker).filter(
            LoanApplicationStepTracker.application_id == application.id
        ).first()

        if not tracker:
            tracker = LoanApplicationStepTracker(
                application_id=application.id,
                current_step=LoanApplicationStep.EMI_CALCULATED.value
            )
            db.add(tracker)

        # ✅ UPDATE STEP
        tracker.current_step = LoanApplicationStep.EMI_CALCULATED.value
        application.current_step = LoanApplicationStep.EMI_CALCULATED.value

        db.commit()


    # =====================================================
    # HELPERS
    # =====================================================
    @staticmethod
    def _get_verified_eligible_amount(db: Session, user_id: int) -> float:
        record = LoanCalculationRepository.get_eligibility_record(db, user_id)

        if not record:
            raise ValueError("No eligibility record found. Please complete eligibility check first.")

        if record.eligibility_status != "ELIGIBLE":
            raise ValueError(f"Not eligible. Reason: {record.failure_reason or 'failed'}")

        eligible_amount = float(record.max_eligible_amount or 0)

        if eligible_amount < MIN_LOAN_AMOUNT:
            raise ValueError(
                f"Eligible amount ₹{eligible_amount:,.0f} is below minimum ₹{MIN_LOAN_AMOUNT:,}"
            )

        return eligible_amount


    @staticmethod
    def _validate_tenure(tenure_months: int) -> None:
        if tenure_months not in ALLOWED_TENURES:
            raise ValueError(f"Tenure must be one of {ALLOWED_TENURES}")


    @staticmethod
    def _monthly_rate() -> float:
        return (ANNUAL_INTEREST_RATE / 12) / 100


    @staticmethod
    def _calculate_emi(principal: float, tenure_months: int) -> float:
        r = LoanCalculationService._monthly_rate()
        n = tenure_months
        emi = (principal * r * pow(1 + r, n)) / (pow(1 + r, n) - 1)
        return round(emi, 2)


    @staticmethod
    def _build_amortization_schedule(principal: float, tenure_months: int) -> list[dict]:

        r        = LoanCalculationService._monthly_rate()
        emi      = LoanCalculationService._calculate_emi(principal, tenure_months)
        balance  = principal
        schedule = []

        for month in range(1, tenure_months + 1):
            interest_part  = round(balance * r, 2)
            principal_part = round(emi - interest_part, 2)
            balance        = round(balance - principal_part, 2)

            if month == tenure_months:
                principal_part = round(principal_part + balance, 2)
                balance = 0.0

            schedule.append({
                "month": month,
                "emi": emi,
                "principal": principal_part,
                "interest": interest_part,
                "balance": max(balance, 0.0),
            })

        return schedule


    # =====================================================
    # MAIN FUNCTION
    # =====================================================
    @staticmethod
    def calculate_and_save(
        db: Session,
        user_id: int,
        tenure_months: int,
    ) -> dict:

        eligible_amount = LoanCalculationService._get_verified_eligible_amount(db, user_id)
        LoanCalculationService._validate_tenure(tenure_months)

        loan_amount = eligible_amount

        monthly_emi = LoanCalculationService._calculate_emi(loan_amount, tenure_months)
        total_repayment = round(monthly_emi * tenure_months, 2)
        total_interest  = round(total_repayment - loan_amount, 2)

        amortization_schedule = LoanCalculationService._build_amortization_schedule(
            loan_amount, tenure_months
        )

        record = LoanCalculationRepository.upsert(
            db=db,
            user_id=user_id,
            requested_amount=loan_amount,
            tenure_months=tenure_months,
            eligible_amount=eligible_amount,
            interest_rate_pa=ANNUAL_INTEREST_RATE,
            monthly_emi=monthly_emi,
            total_repayment=total_repayment,
            total_interest=total_interest,
        )

        # =====================================================
        # 🔥 MOVE STEP FORWARD (FINAL FIX)
        # =====================================================
        LoanCalculationService._update_emi_step(db, user_id)

        return {
            "requested_amount": loan_amount,
            "tenure_months": tenure_months,
            "monthly_emi": monthly_emi,
            "total_repayment": total_repayment,
            "total_interest": total_interest,
            "amortization_schedule": amortization_schedule,
            "record": record,
        }


    @staticmethod
    def get_calculation(db: Session, user_id: int) -> LoanCalculation | None:
        return LoanCalculationRepository.get_by_user_id(db, user_id)