from sqlalchemy.orm import Session
from models.Profile_KYC.user_profile import UserProfile
from models.Auth.user import User
from typing import Optional, List

class UserRepository:
    @staticmethod
    def get_module1_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[UserProfile]:
        return db.query(UserProfile).filter(UserProfile.email == email).first()

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Optional[UserProfile]:
        return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    @staticmethod
    def get_by_pan_number(db: Session, pan_number: str) -> Optional[UserProfile]:
        return db.query(UserProfile).filter(UserProfile.pan_number == pan_number).first()
    
    @staticmethod
    def get_by_aadhaar_number(db: Session, aadhaar_number: str) -> Optional[UserProfile]:
        return db.query(UserProfile).filter(UserProfile.aadhaar_number == aadhaar_number).first()

    @staticmethod
    def create_user(db: Session, user: UserProfile) -> UserProfile:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user(db: Session, user: UserProfile) -> UserProfile:
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def save(db: Session) -> None:
        db.commit()

    @staticmethod
    def get_all_users(db: Session, limit: int = 50, offset: int = 0) -> List[UserProfile]:
        return db.query(UserProfile).order_by( UserProfile.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_users_by_kyc_status(db: Session, kyc_status: str, limit: int = 50, offset: int = 0) -> List[UserProfile]:
        return db.query(UserProfile).filter( UserProfile.kyc_status == kyc_status).order_by(UserProfile.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def count_all_users(db: Session) -> int:
        return db.query(UserProfile).count()

    @staticmethod
    def count_by_kyc_status(db: Session, kyc_status: str) -> int:
        return db.query(UserProfile).filter(UserProfile.kyc_status == kyc_status).count()