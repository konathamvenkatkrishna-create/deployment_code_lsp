import os
import requests
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
 
from models.Eligibility.credit_profile import CreditProfile
from models.Eligibility.credit_account import CreditAccount
from models.Profile_KYC.kyc_pan_verification import KYCPANVerification
 
 
TRANSUNION_API_URL = os.getenv("TRANSUNION_API_URL")
TRANSUNION_API_KEY = os.getenv("TRANSUNION_API_KEY")
 
 
class CreditRepository:
 
    @staticmethod
    def get_latest_credit_profile(db: Session, user_id: str) -> CreditProfile | None:
        return (
            db.query(CreditProfile)
            .filter(CreditProfile.user_id == user_id)
            .order_by(CreditProfile.pulled_at.desc())
            .first()
        )
 
    @staticmethod
    def get_latest_verified_pan(db: Session, user_id: int) -> str:
        pan_record = (
            db.query(KYCPANVerification)
            .filter(
                KYCPANVerification.user_id == user_id,
                KYCPANVerification.status == "VERIFIED",
            )
            .order_by(desc(KYCPANVerification.created_at))
            .first()
        )
 
        if not pan_record:
            raise HTTPException(
                status_code=400,
                detail="No VERIFIED PAN found for this user. Complete KYC first.",
            )
 
        return pan_record.pan_number
 
    @staticmethod
    def _call_transunion_api(
        pan_number: str,
        inquiry_type: str,  
        purpose: str,
    ) -> dict:
        if not TRANSUNION_API_KEY:
            raise EnvironmentError(
                "TRANSUNION_API_KEY is not set. Add it to your .env file."
            )
 
        headers = {
            "Authorization": f"Bearer {TRANSUNION_API_KEY}",
            "Content-Type": "application/json",
        }
 
        payload = {
            "pan": pan_number,
            "consent": True,
            "purpose": purpose,
            "inquiryType": inquiry_type,
        }
 
        try:
            resp = requests.post(
                TRANSUNION_API_URL,
                json=payload,
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
        except requests.Timeout:
            raise HTTPException(
                status_code=504,
                detail="TransUnion API timed out. Please retry.",
            )
        except requests.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"TransUnion API error {exc.response.status_code}: {exc.response.text}",
            )
 
        return resp.json()
 
    @staticmethod
    def _persist_credit_profile(
        db: Session,
        user_id: str,
        pan_number: str,
        data: dict,
        pull_type: str,
    ) -> CreditProfile:
        """
        Parses the TransUnion API response, saves CreditProfile
        and all CreditAccount rows to the DB.
        """
        raw_accounts = data.get("accounts", [])
        active_accounts = [a for a in raw_accounts if a.get("status") == "ACTIVE"]
        total_existing_emi = sum(float(a.get("emiAmount", 0)) for a in active_accounts)
 
        profile = CreditProfile(
            user_id=user_id,
            pan_number=pan_number,
            bureau_name=data.get("bureau", "TransUnion"),
            credit_score=data["creditScore"],
            report_reference_id=data.get("reportId"),
            pull_type=pull_type,                     # NEW FIELD — add to your model/migration
            total_active_loans=len(active_accounts),
            total_existing_emi=total_existing_emi,
            bureau_raw_response=data,
            pulled_at=datetime.utcnow(),
        )
        db.add(profile)
        db.flush()   # populate profile.id before inserting child accounts
 
        for acc in raw_accounts:
            db.add(CreditAccount(
                credit_profile_id=profile.id,
                loan_type=acc.get("loanType"),
                emi_amount=float(acc.get("emiAmount", 0)),
                status=acc.get("status"),
            ))
 
        db.commit()
        db.refresh(profile)
        return profile
 
    @staticmethod
    def soft_pull(db: Session, user_id: str) -> CreditProfile:
        pan_number = CreditRepository.get_latest_verified_pan(db, user_id)
 
        data = CreditRepository._call_transunion_api(
            pan_number=pan_number,
            inquiry_type="SOFT",
            purpose="PRE_QUALIFICATION",
        )
 
        return CreditRepository._persist_credit_profile(
            db=db,
            user_id=user_id,
            pan_number=pan_number,
            data=data,
            pull_type="SOFT",
        )
 
    @staticmethod
    def hard_pull(db: Session, user_id: str) -> CreditProfile:
        pan_number = CreditRepository.get_latest_verified_pan(db, user_id)
 
        data = CreditRepository._call_transunion_api(
            pan_number=pan_number,
            inquiry_type="HARD",
            purpose="LOAN_UNDERWRITING",
        )
 
        return CreditRepository._persist_credit_profile(
            db=db,
            user_id=user_id,
            pan_number=pan_number,
            data=data,
            pull_type="HARD",
        )
 
    @staticmethod
    def create_dummy_credit_profile(
        db: Session,
        user_id: str,
        pull_type: str = "SOFT",
    ) -> CreditProfile:
        pan_number = CreditRepository.get_latest_verified_pan(db, user_id)
 
        import random
 
        dummy_score = random.choice([620, 670, 710, 760, 810])
 
        dummy_accounts_map = {
            620: [
                {"loan_type": "PL", "emi_amount": 4000, "status": "ACTIVE"},
                {"loan_type": "CC", "emi_amount": 2000, "status": "ACTIVE"},
            ],
            670: [{"loan_type": "PL", "emi_amount": 2000, "status": "ACTIVE"}],
            710: [{"loan_type": "AUTO", "emi_amount": 3500, "status": "ACTIVE"}],
            760: [
                {"loan_type": "HL", "emi_amount": 5000, "status": "ACTIVE"},
                {"loan_type": "PL", "emi_amount": 1000, "status": "CLOSED"},
            ],
            810: [],
        }
 
        accounts_data = dummy_accounts_map.get(dummy_score, [])
        active_accounts = [a for a in accounts_data if a["status"] == "ACTIVE"]
        total_existing_emi = sum(a["emi_amount"] for a in active_accounts)
 
        profile = CreditProfile(
            user_id=user_id,
            pan_number=pan_number,
            bureau_name="TransUnion (Dummy)",
            credit_score=dummy_score,
            report_reference_id=f"DUMMY-{pan_number}",
            pull_type=pull_type,
            total_active_loans=len(active_accounts),
            total_existing_emi=total_existing_emi,
            bureau_raw_response={"dummy": True, "score": dummy_score},
            pulled_at=datetime.utcnow(),
        )
        db.add(profile)
        db.flush()
 
        for acc in accounts_data:
            db.add(CreditAccount(
                credit_profile_id=profile.id,
                loan_type=acc["loan_type"],
                emi_amount=acc["emi_amount"],
                status=acc["status"],
            ))
 
        db.commit()
        db.refresh(profile)
        return profile
 