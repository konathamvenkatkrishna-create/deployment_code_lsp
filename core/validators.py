import re

def validate_mobile_number(v: str,) -> str:
    if not re.fullmatch(r"\+91[6-9]\d{9}", v):
        raise ValueError(f"Mobile number must start with +91 and contain 10 digits (6-9 start)")
    return v


def validate_otp(v: str) -> str:
    if not re.fullmatch(r"\d{6}", v):
        raise ValueError("OTP must be exactly 6 digits")
    return v


def validate_device_id(v: str | None) -> str | None:
    if v is not None and not (6 <= len(v) <= 64):
        raise ValueError("Device ID must be between 6 and 64 characters")
    return v


def validate_password(v: str) -> str:
    if not (8 <= len(v) <= 64):
        raise ValueError("Password must be 8–64 characters long")

    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", v):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one number")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
        raise ValueError("Password must contain at least one special character")

    return v
def validate_username(v: str) -> str:
    if not re.fullmatch(r"^[A-Za-z0-9_.]{3,30}$", v):
        raise ValueError("Username must be 3–30 characters and contain only letters, numbers, underscore")
    return v


def validate_gst_number(v: str | None) -> str | None:
    if v is None:
        return v

    v = v.upper().strip()

    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$"
    if not re.fullmatch(pattern, v):
        raise ValueError("Invalid GST format")

    return v


def validate_address(v: str | None) -> str | None:
    if v is None:
        return v
    return v.strip()


def validate_company_name(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("Company name cannot be empty")
    return v

def validate_credit_score(cls, v):
    if v < 300 or v > 900:
        raise ValueError("Credit score must be between 300 and 900")
    return v

def validate_interest_rate(cls, v):
    if v <= 0 or v > 100:
        raise ValueError("Interest rate must be between 0 and 100")
    return v

def validate_max_amount(cls, v):
    if v <= 0 or v > 20000:
        raise ValueError("Max amount must be a positive number")
    return v