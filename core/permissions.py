from fastapi import Depends, HTTPException, status
from core.auth import get_current_user


def super_admin_required(
    current_user=Depends(get_current_user)
):
    if current_user.role not in ("SUPER_ADMIN", "SUPERADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperAdmin allowed"
        )
    return current_user


def admin_required(
    current_user=Depends(get_current_user)
):
    if current_user.role not in (
        "ADMIN",
        "SUPER_ADMIN",
        "SUPERADMIN"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_roles(
    current_user=Depends(get_current_user)
):
    if current_user.role not in (
        "USER",
        "ADMIN",
        "SUPER_ADMIN",
        "SUPERADMIN"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User access required"
        )
    return current_user