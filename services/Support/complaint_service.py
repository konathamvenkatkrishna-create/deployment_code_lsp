import logging

from fastapi import HTTPException

from sqlalchemy.orm import Session

from datetime import datetime

from core.email_service import sendmail

from models.Support.complaint import (
    Complaint
)

from models.Support.complaint_history import (
    ComplaintHistory
)

from models.Profile_KYC.user_profile import (
    UserProfile
)

from core.enums import (
    ComplaintStatusEnum
)


# =====================================================
# LOGGER
# =====================================================
logger = logging.getLogger(__name__)


# =====================================================
# GENERATE COMPLAINT NUMBER
# =====================================================
def generate_complaint_number(
    db: Session
):

    latest = db.query(
        Complaint
    ).order_by(
        Complaint.id.desc()
    ).first()

    next_id = 1

    if latest:

        next_id = latest.id + 1

    today = datetime.utcnow().strftime(
        "%Y%m%d"
    )

    return f"CMP-{today}-{next_id:05d}"


# =====================================================
# SEND EMAIL HELPER
# =====================================================
def send_complaint_email(

    to_email: str,

    subject: str,

    body: str
):

    try:

        sendmail(

            to=to_email,

            subject=subject,

            body=body
        )

    except Exception as e:

        logger.error(
            f"Email sending failed: {str(e)}"
        )


# =====================================================
# USER - CREATE COMPLAINT
# =====================================================
def register_complaint(

    db: Session,

    payload,

    current_user,

    attachment_path=None
):

    # =============================================
    # FETCH USER PROFILE
    # =============================================
    user_profile = db.query(
        UserProfile
    ).filter(
        UserProfile.user_id
        == current_user.id
    ).first()

    if not user_profile:

        raise HTTPException(

            status_code=404,

            detail=(
                "User profile not found. "
                "Please complete profile first."
            )
        )

    # =============================================
    # EMAIL CHECK
    # =============================================
    if not user_profile.email:

        raise HTTPException(

            status_code=400,

            detail=(
                "Email not found "
                "in user profile."
            )
        )

    if user_profile.email_verified is False:

        raise HTTPException(

            status_code=400,

            detail=(
                "Please verify your email "
                "before raising a complaint."
            )
        )

    try:

        # =========================================
        # CREATE COMPLAINT
        # =========================================
        complaint = Complaint(

            complaint_number=
                generate_complaint_number(db),

            user_id=
                current_user.id,

            application_id=
                getattr(
                    payload,
                    "application_id",
                    None
                ),

            category=(
                payload.category.value
                if hasattr(
                    payload.category,
                    "value"
                )
                else payload.category
            ),

            subject=
                payload.subject,

            description=
                payload.description,

            priority=(
                payload.priority.value
                if hasattr(
                    payload.priority,
                    "value"
                )
                else payload.priority
            ),

            status=
                ComplaintStatusEnum.OPEN.value,

            attachment_url=
                attachment_path,

            created_at=
                datetime.utcnow(),

            updated_at=
                datetime.utcnow()
        )

        db.add(complaint)

        db.flush()

        db.refresh(complaint)

        print(
            "Complaint Created:",
            complaint.id
        )

        if not complaint.id:

            raise HTTPException(

                status_code=500,

                detail="Complaint creation failed"
            )

        # =========================================
        # CREATE HISTORY
        # =========================================
        history = ComplaintHistory(

            complaint_id=
                complaint.id,

            old_status=
                None,

            new_status=
                ComplaintStatusEnum.OPEN.value,

            changed_by=
                str(current_user.id),

            comment=
                "Complaint created by user"
        )

        db.add(history)

        db.commit()

        db.refresh(complaint)

    except HTTPException:

        db.rollback()

        raise

    except Exception as e:

        db.rollback()

        print(
            "Complaint Save Error:",
            str(e)
        )

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )

    # =============================================
    # SEND EMAIL
    # =============================================
    subject = (
        f"Complaint Registered Successfully - "
        f"{complaint.complaint_number}"
    )

    body = f"""
Hello {user_profile.full_name},

Your complaint has been registered successfully.

Complaint Number: {complaint.complaint_number}
Category: {complaint.category}
Subject: {complaint.subject}
Priority: {complaint.priority}
Status: {complaint.status}

Our support team will review your complaint and update you soon.

Thank you,
LSP Support Team
"""

    send_complaint_email(

        to_email=
            user_profile.email,

        subject=
            subject,

        body=
            body
    )

    # =============================================
    # SERIALIZED RESPONSE
    # =============================================
    return {

        "id":
            complaint.id,

        "complaint_number":
            complaint.complaint_number,

        "user_id":
            complaint.user_id,

        "application_id":
            complaint.application_id,

        "category":
            complaint.category,

        "subject":
            complaint.subject,

        "description":
            complaint.description,

        "priority":
            complaint.priority,

        "status":
            complaint.status,

        "attachment_url":
            complaint.attachment_url,

        "created_at":
            complaint.created_at,

        "updated_at":
            complaint.updated_at
    }


# =====================================================
# USER - LIST OWN COMPLAINTS
# =====================================================
def list_complaints(

    db: Session,

    current_user
):

    print(
        "Fetching complaints for user:",
        current_user.id
    )

    complaints = db.query(
        Complaint
    ).filter(

        Complaint.user_id
        == current_user.id

    ).order_by(
        Complaint.created_at.desc()
    ).all()

    return complaints


# =====================================================
# USER - GET OWN COMPLAINT DETAIL
# =====================================================
def get_complaint_detail(

    db: Session,

    complaint_id: int,

    current_user
):

    complaint = db.query(
        Complaint
    ).filter(

        Complaint.id
        == complaint_id,

        Complaint.user_id
        == current_user.id

    ).first()

    if not complaint:

        raise HTTPException(

            status_code=404,

            detail="Complaint not found"
        )

    return complaint


# =====================================================
# SUPER ADMIN - LIST ALL COMPLAINTS
# =====================================================
def admin_list_all_complaints_grouped_by_user(

    db: Session,

    current_user
):

    complaints = db.query(
        Complaint
    ).order_by(
        Complaint.created_at.desc()
    ).all()

    grouped_data = {}

    for complaint in complaints:

        user_id = complaint.user_id

        if user_id not in grouped_data:

            grouped_data[user_id] = {

                "user_id":
                    user_id,

                "total_complaints":
                    0,

                "complaints":
                    []
            }

        grouped_data[user_id][
            "total_complaints"
        ] += 1

        grouped_data[user_id][
            "complaints"
        ].append({

            "id":
                complaint.id,

            "complaint_number":
                complaint.complaint_number,

            "category":
                complaint.category,

            "subject":
                complaint.subject,

            "priority":
                complaint.priority,

            "status":
                complaint.status,

            "created_at":
                complaint.created_at,

            "updated_at":
                complaint.updated_at
        })

    return {

        "total_users":
            len(grouped_data),

        "data":
            list(grouped_data.values())
    }


# =====================================================
# ADMIN - COMPLAINT DETAIL
# =====================================================
def admin_get_complaint_detail(

    db: Session,

    complaint_id: int,

    current_user
):

    complaint = db.query(
        Complaint
    ).filter(
        Complaint.id
        == complaint_id
    ).first()

    if not complaint:

        raise HTTPException(

            status_code=404,

            detail="Complaint not found"
        )

    return complaint


# =====================================================
# SUPPORT - LIST ALL COMPLAINTS
# =====================================================
def support_list_all_complaints(

    db: Session,

    current_user
):

    complaints = db.query(
        Complaint
    ).order_by(
        Complaint.created_at.desc()
    ).all()

    return {

        "total_complaints":
            len(complaints),

        "open":
            sum(
                1 for c in complaints
                if c.status
                == ComplaintStatusEnum.OPEN.value
            ),

        "in_progress":
            sum(
                1 for c in complaints
                if c.status
                == ComplaintStatusEnum.IN_PROGRESS.value
            ),

        "resolved":
            sum(
                1 for c in complaints
                if c.status
                == ComplaintStatusEnum.RESOLVED.value
            ),

        "closed":
            sum(
                1 for c in complaints
                if c.status
                == ComplaintStatusEnum.CLOSED.value
            ),

        "complaints":
            complaints
    }


# =====================================================
# SUPPORT - GET COMPLAINT DETAIL
# =====================================================
def support_get_complaint_detail(

    db: Session,

    complaint_id: int,

    current_user
):

    complaint = db.query(
        Complaint
    ).filter(
        Complaint.id
        == complaint_id
    ).first()

    if not complaint:

        raise HTTPException(

            status_code=404,

            detail="Complaint not found"
        )

    return complaint


# =====================================================
# SUPPORT - UPDATE COMPLAINT STATUS
# =====================================================
def support_update_complaint_status(

    db: Session,

    complaint_id: int,

    payload,

    current_user
):

    complaint = db.query(
        Complaint
    ).filter(
        Complaint.id
        == complaint_id
    ).first()

    if not complaint:

        raise HTTPException(

            status_code=404,

            detail="Complaint not found"
        )

    current_status = complaint.status

    new_status = (

        payload.status.value

        if hasattr(
            payload.status,
            "value"
        )

        else payload.status
    )

    allowed_transitions = {

        ComplaintStatusEnum.OPEN.value: [

            ComplaintStatusEnum.IN_PROGRESS.value,
        ],

        ComplaintStatusEnum.IN_PROGRESS.value: [

            ComplaintStatusEnum.RESOLVED.value,

            ComplaintStatusEnum.CLOSED.value,
        ],

        ComplaintStatusEnum.RESOLVED.value: [

            ComplaintStatusEnum.CLOSED.value,
        ],

        ComplaintStatusEnum.CLOSED.value: [],
    }

    if new_status not in allowed_transitions.get(
        current_status,
        []
    ):

        raise HTTPException(

            status_code=400,

            detail=(
                f"Invalid status change "
                f"from {current_status} "
                f"to {new_status}"
            )
        )

    complaint.status = new_status

    complaint.updated_at = datetime.utcnow()

    history = ComplaintHistory(

        complaint_id=
            complaint.id,

        old_status=
            current_status,

        new_status=
            new_status,

        changed_by=
            str(current_user.id),

        comment=
            payload.comment
    )

    db.add(history)

    db.commit()

    db.refresh(complaint)

    # =============================================
    # FETCH USER PROFILE
    # =============================================
    user_profile = db.query(
        UserProfile
    ).filter(
        UserProfile.user_id
        == complaint.user_id
    ).first()

    if (

        user_profile

        and user_profile.email

        and user_profile.email_verified
    ):

        subject = (
            f"Complaint Status Updated - "
            f"{complaint.complaint_number}"
        )

        body = f"""
Hello {user_profile.full_name},

Your complaint status has been updated.

Complaint Number: {complaint.complaint_number}
Subject: {complaint.subject}
Old Status: {current_status}
New Status: {complaint.status}

Support Comment:
{payload.comment if payload.comment else "No comment provided."}

Thank you,
LSP Support Team
"""

        send_complaint_email(

            to_email=
                user_profile.email,

            subject=
                subject,

            body=
                body
        )

    return {

        "message":
            "Complaint status updated successfully",

        "complaint_id":
            complaint.id,

        "complaint_number":
            complaint.complaint_number,

        "old_status":
            current_status,

        "new_status":
            complaint.status,

        "updated_by":
            current_user.id
    }