import httpx
from fastapi import HTTPException
from core.config import settings

_BASE    = "https://api.razorpay.com/v1"
_TIMEOUT = httpx.Timeout(15.0)

def _auth() -> tuple[str, str]:
    return (settings.PAYMENT_KEY_ID, settings.PAYMENT_KEY_SECRET)

def _is_test_mode() -> bool:
    return bool(
        settings.PAYMENT_KEY_ID
        and settings.PAYMENT_KEY_ID.startswith("rzp_test")
    )

def _post(endpoint: str, payload: dict) -> dict:
    try:
        resp = httpx.post(
            f"{_BASE}{endpoint}",
            json=payload,
            auth=_auth(),
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Razorpay service timed out. Please try again.",
        )
    except httpx.HTTPStatusError as e:
        try:
            desc = e.response.json().get("error", {}).get("description", "Razorpay request failed")
        except Exception:
            desc = "Razorpay request failed"
        raise HTTPException(status_code=400, detail=desc)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach Razorpay. Please try again later.",
        )


# ============================================================
# Step 1 — Create Contact
# ============================================================
def create_contact(name: str, email: str, contact: str) -> str:
    """
    POST /v1/contacts
    Returns contact_id  e.g. "cont_XXXXXXXXXXXXXXX"
    """
    data = _post("/contacts", {
        "name":    name,
        "email":   email,
        "contact": contact,
        "type":    "customer",
    })
    contact_id = data.get("id")
    if not contact_id:
        raise HTTPException(502, "Razorpay did not return a contact ID.")
    return contact_id


# ============================================================
# Step 2 — Create Fund Account
# ============================================================
def create_fund_account(
    contact_id: str,
    name: str,
    account_number: str,
    ifsc: str,
) -> str:
    """
    POST /v1/fund_accounts
    Returns fund_account_id  e.g. "fa_XXXXXXXXXXXXXXX"
    """
    data = _post("/fund_accounts", {
        "contact_id":   contact_id,
        "account_type": "bank_account",
        "bank_account": {
            "name":           name,
            "ifsc":           ifsc,
            "account_number": account_number,
        },
    })
    fund_account_id = data.get("id")
    if not fund_account_id:
        raise HTTPException(502, "Razorpay did not return a fund account ID.")
    return fund_account_id


# ============================================================
# Step 3 — Validate Fund Account (Penny Drop)
# ============================================================
def validate_fund_account(fund_account_id: str, account_holder_name: str) -> dict:
    """
    POST /v1/fund_accounts/validations

    Test mode behaviour (known Razorpay limitation):
      - account_status  → always "inactive" or empty — NOT reliable
      - registered_name → always empty               — NOT reliable
      - Fix: if API call succeeds → force active + use submitted name

    Live mode behaviour:
      - account_status  → real "active" / "inactive"
      - registered_name → real name from bank
      - Full validation applies

    Returns normalised dict:
    {
        "razorpay_status":  "completed" | "failed",
        "account_status":   "active"    | "inactive",
        "registered_name":  "John Doe",
        "validation_id":    "fav_...",
    }
    """
    test_mode = _is_test_mode()

    # Build payload
    payload: dict = {
        "fund_account": {
            "id": fund_account_id,
        },
        "amount":   100,    # ₹1 in paise — required by Razorpay even in test mode
        "currency": "INR",
    }

    # Live mode only — source account number required
    if not test_mode:
        if not settings.PAYMENT_ACCOUNT_NUMBER:
            raise HTTPException(
                500,
                "PAYMENT_ACCOUNT_NUMBER is not set in .env. Required for live mode.",
            )
        payload["account_number"] = settings.PAYMENT_ACCOUNT_NUMBER

    data = _post("/fund_accounts/validations", payload)

    status        = data.get("status", "")
    results       = data.get("results", {})
    validation_id = data.get("id", "")

    if test_mode:
        is_success = status in ("created", "completed")
        return {
            "razorpay_status": "completed" if is_success else "failed",
            "account_status":  "active",             # force active in test mode
            "registered_name": account_holder_name,  # use submitted name → 100% name match
            "validation_id":   validation_id,
        }
    else:
        # ── LIVE MODE ─────────────────────────────────────────────
        # Use actual values returned by Razorpay
        account_status  = results.get("account_status", "inactive")
        registered_name = results.get("registered_name", "")
        is_success      = status == "completed"
        return {
            "razorpay_status": "completed" if is_success else "failed",
            "account_status":  account_status,
            "registered_name": registered_name,
            "validation_id":   validation_id,
        }