from sqlalchemy.orm import Session
from models.Auth.user import User

class UserRepository:

    @staticmethod
    def get_user_by_id(db: Session, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_mobile(db: Session, mobile: str):
        return db.query(User).filter(User.mobile == mobile).first()

    @staticmethod
    def create_user(db: Session, user: User):
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
