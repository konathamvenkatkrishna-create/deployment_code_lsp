# routers/reminder_settings_router.py
 
from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session
 
from core.database import get_db

from core.dependencies import require_roles

from models.Auth.user import User
 
from schemas.Repayment.reminder_schema import (

    ReminderSettingsUpdate,

    ReminderSettingsResponse,

)
 
from services.Repayment.remainder_settings_service import ReminderSettingsService
 
router = APIRouter(prefix="/reminders/settings", tags=["Reminder Settings"])
 
 
@router.get("", response_model=ReminderSettingsResponse)

def get_settings(

    db: Session = Depends(get_db),

    user: User = Depends(require_roles(["USER"]))

):

    return ReminderSettingsService.get_or_create(user.id, db)
 
 
@router.patch("", response_model=ReminderSettingsResponse)

def update_settings(

    payload: ReminderSettingsUpdate,

    db: Session = Depends(get_db),

    user: User = Depends(require_roles(["USER"]))

):

    settings = ReminderSettingsService.get_or_create(user.id, db)
 
    return ReminderSettingsService.update(

        settings,

        payload.dict(exclude_none=True),

        db

    )
 