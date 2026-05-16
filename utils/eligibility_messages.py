def map_failure_reason(reason: str, status: str) -> str:
    if status == "ELIGIBLE":
        return "You are eligible for the requested loan."

    mapping = {
        "LOW_CREDIT_SCORE": "Your credit score is below the required threshold (650).",
        "FOIR_EXCEEDED": "Your existing EMIs exceed the allowed repayment capacity.",
        "INVALID_INCOME": "Income details are invalid or missing.",
        "NO_EMI_CAPACITY": "You currently do not have EMI repayment capacity.",
        "CREDIT_PROFILE_NOT_FOUND": "Credit data not available. Please retry later."
    }

    return mapping.get(reason, "You are not eligible at this time.")










