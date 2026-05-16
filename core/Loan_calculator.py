from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta
from datetime import date

MIN_LOAN_AMOUNT = Decimal("5000")
MAX_LOAN_AMOUNT = Decimal("20000")

ALLOWED_TENURES = [3, 6, 9, 12]

PROCESSING_FEE_PERCENT = Decimal("5")
GST_RATE = Decimal("18")


def to_decimal(value):
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def validate_loan_request(principal, tenure_months) -> Decimal:
    if principal is None or tenure_months is None:
        raise ValueError("Loan amount and tenure are required")

    try:
        principal = to_decimal(principal)
    except Exception:
        raise ValueError("Loan amount must be a valid number")

    if principal < MIN_LOAN_AMOUNT or principal > MAX_LOAN_AMOUNT:
        raise ValueError(
            f"Loan amount must be between ₹{MIN_LOAN_AMOUNT} and ₹{MAX_LOAN_AMOUNT}"
        )

    if tenure_months not in ALLOWED_TENURES:
        raise ValueError(f"Tenure must be one of {ALLOWED_TENURES}")

    return principal


def calculate_emi(principal: Decimal, annual_rate: Decimal, tenure: int) -> Decimal:
    principal = to_decimal(principal)
    annual_rate = to_decimal(annual_rate)

    monthly_rate = annual_rate / Decimal("100") / Decimal("12")

    if monthly_rate == 0:
        return (principal / tenure).quantize(Decimal("0.01"))

    r = monthly_rate
    n = tenure

    factor = (Decimal("1") + r) ** n

    emi = (principal * r * factor) / (factor - Decimal("1"))

    return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_processing_fee(principal: Decimal) -> dict:
    principal = to_decimal(principal)

    processing_fee = (
        principal * PROCESSING_FEE_PERCENT / Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    gst_on_fee = (
        processing_fee * GST_RATE / Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    total_charges = (processing_fee + gst_on_fee).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    return {
        "processing_fee": processing_fee,
        "gst_on_processing_fee": gst_on_fee,
        "total_processing_charges": total_charges
    }


def generate_schedule(
    principal: Decimal,
    annual_rate: Decimal,
    tenure: int,
    first_emi_date: date
):
    principal = to_decimal(principal)
    annual_rate = to_decimal(annual_rate)

    emi_fixed = calculate_emi(principal, annual_rate, tenure)

    monthly_rate = annual_rate / Decimal("100") / Decimal("12")

    remaining = principal
    schedule = []

    for emi_number in range(1, tenure + 1):

        opening = remaining

        interest = (opening * monthly_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        principal_component = (emi_fixed - interest).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if emi_number == tenure:
            principal_component = opening  # adjust last EMI

        emi_to_use = (principal_component + interest).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        closing = (opening - principal_component).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        closing = max(closing, Decimal("0.00"))

        # gst_on_interest = (PROCESSING_FEE_PERCENT * GST_RATE / Decimal("100")).quantize(
        #     Decimal("0.01"), rounding=ROUND_HALF_UP
        # )

        due_date = first_emi_date + relativedelta(months=emi_number - 1)
        due_date = due_date.replace(day=min(first_emi_date.day, 28))

        schedule.append({
            "emi_number": emi_number,
            "due_date": due_date,
            "opening_principal": float(opening),
            "principal_component": float(principal_component),
            "interest_component": float(interest),
            # "gst_on_interest": float(gst_on_interest),
            "emi_amount": float(emi_to_use),
            "closing_principal": float(closing)
        })

        remaining = closing

    return schedule

def calculate_loan_summary(
    principal,
    interest_rate,
    tenure_months,
    first_emi_date: date
) -> dict:

    principal = validate_loan_request(principal, tenure_months)
    interest_rate = to_decimal(interest_rate)

    emi = calculate_emi(principal, interest_rate, tenure_months)

    schedule = generate_schedule(
        principal,
        interest_rate,
        tenure_months,
        first_emi_date
    )

    charges = calculate_processing_fee(principal)

    total_repayment = (emi * tenure_months).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    total_interest = total_repayment - principal

    return {
        "emi": float(emi),
        "total_amount": float(total_repayment),
        "processing_fee": float(charges["processing_fee"]),
        "gst_amount": float(charges["gst_on_processing_fee"]),
        "total_interest": float(total_interest),
        "schedule": schedule
    }