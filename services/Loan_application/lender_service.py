from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
 
from models.Auth.lender import Lender
from models.Loan_application.loan_application import LoanApplication
from core.enums import LoanApplicationStatus, LoanApplicationStep, enum_value
 
 
class LenderService:
 
    # ---------------------------------------------------
    # ✅ GET APPLICATIONS FOR LENDER DASHBOARD
    # ---------------------------------------------------
    @staticmethod
    def get_lender_applications(
        db: Session,
        user_id: int,
        status: str = None
    ):
 
        lender = db.query(Lender).filter(
            Lender.user_id == user_id
        ).first()
 
        if not lender:
            raise HTTPException(404, "Lender not found")
 
        query = db.query(LoanApplication).filter(
            LoanApplication.lender_id == lender.id,
            LoanApplication.is_submitted == True
        )
 
        if status:
            try:
                query = query.filter(
                    LoanApplication.application_status == enum_value(status)
                )
            except Exception:
                raise HTTPException(400, "Invalid status value")
 
        applications = query.order_by(
            LoanApplication.updated_at.desc()
        ).all()
 
        return applications
 
 
    # ---------------------------------------------------
    # ✅ APPROVE APPLICATION
    # ---------------------------------------------------
    @staticmethod
    def approve_application(
        db: Session,
        application_id: int,
        user_id: int
    ):
 
        lender = db.query(Lender).filter(
            Lender.user_id == user_id
        ).first()
 
        if not lender:
            raise HTTPException(404, "Lender not found")
 
        application = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).with_for_update().first()
 
        if not application:
            raise HTTPException(404, "Application not found")
 
        if application.lender_id != lender.id:
            raise HTTPException(403, "You are not assigned to this application")
 
        if not application.is_submitted:
            raise HTTPException(400, "Application not submitted")
 
        if application.application_status == enum_value(LoanApplicationStatus.APPROVED):
            raise HTTPException(400, "Application already approved")
 
        if application.application_status == enum_value(LoanApplicationStatus.REJECTED):
            raise HTTPException(400, "Application already rejected")
 
        if application.application_status != enum_value(LoanApplicationStatus.SUBMITTED):
            raise HTTPException(400, "Application not in submitted state")
 
        # ✅ UPDATE
        application.application_status = enum_value(LoanApplicationStatus.APPROVED)
        application.lender_decision = "APPROVED"
        application.current_step = enum_value(LoanApplicationStep.COMPLETED)
        application.approved_at = datetime.utcnow()
        application.reviewed_at = datetime.utcnow()
        application.lender_decision_at = datetime.utcnow()
        db.commit()
        db.refresh(application)
 
        return {
            "message": "Application approved successfully",
            "application_id": application.id,
            "status": "APPROVED"
        }
 
 
    # ---------------------------------------------------
    # ❌ REJECT APPLICATION (FULLY FIXED)
    # ---------------------------------------------------
    @staticmethod
    def reject_application(
        db: Session,
        application_id: int,
        user_id: int,
        rejection_reason: str
    ):
 
        # ✅ STRICT VALIDATION
        if not rejection_reason or not rejection_reason.strip():
            raise HTTPException(400, "Rejection reason is required")
 
        if len(rejection_reason.strip()) > 500:
            raise HTTPException(400, "Rejection reason too long")
 
        lender = db.query(Lender).filter(
            Lender.user_id == user_id
        ).first()
 
        if not lender:
            raise HTTPException(404, "Lender not found")
 
        application = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).with_for_update().first()
 
        if not application:
            raise HTTPException(404, "Application not found")
 
        if application.lender_id != lender.id:
            raise HTTPException(403, "You are not assigned to this application")
 
        if not application.is_submitted:
            raise HTTPException(400, "Application not submitted")
 
        if application.application_status == enum_value(LoanApplicationStatus.APPROVED):
            raise HTTPException(400, "Application already approved")
 
        if application.application_status == enum_value(LoanApplicationStatus.REJECTED):
            raise HTTPException(400, "Application already rejected")
 
        if application.application_status != enum_value(LoanApplicationStatus.SUBMITTED):
            raise HTTPException(400, "Application not in submitted state")
 
        # ✅ UPDATE
        application.application_status = enum_value(LoanApplicationStatus.REJECTED)
        application.lender_decision = "REJECTED"
 
        # 🔥 CLEAN STORAGE
        application.rejection_reason = rejection_reason.strip()
 
        application.current_step = enum_value(LoanApplicationStep.COMPLETED)
 
        application.rejected_at = datetime.utcnow()
        application.reviewed_at = datetime.utcnow()
 
        db.commit()
        db.refresh(application)
 
        return {
            "message": "Application rejected successfully",
            "application_id": application.id,
            "status": "REJECTED",
            "rejection_reason": application.rejection_reason
        }
 