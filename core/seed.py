from sqlalchemy.orm import Session
from models.Auth.user import User
from core.security import hash_password


def create_default_super_admin(
    db: Session,
    username: str,
    mobile_number: str,
    password: str,
    device_id: str
):

    # ✅ Check using BOTH username & mobile
    existing = db.query(User).filter(
        (User.mobile_number == mobile_number) |
        (User.username == username)
    ).first()

    if existing:
        return existing

    # ✅ Create new admin
    super_admin = User(
        username=username,
        mobile_number=mobile_number,
        password_hash=hash_password(password),
        device_id=device_id,
        role="SUPER_ADMIN",
        is_active=True,
        is_verified=True
    )

    try:
        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)


    except Exception as e:
        db.rollback()
    return super_admin