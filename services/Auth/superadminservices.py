from fastapi import Depends, HTTPException, status
from models.Auth.user import User
from core.dependencies import get_current_user



def super_admin_required(
    current_user: User = Depends(get_current_user),
) -> User:

    if current_user.role not in ("SUPER_ADMIN", "SUPERADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperAdmin can perform this action",
        )

    return current_user


def lender_required(
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["LENDER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lender access required"
        )
    return current_user
