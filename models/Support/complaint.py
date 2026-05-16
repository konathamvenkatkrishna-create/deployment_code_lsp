from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey
)

from sqlalchemy.orm import relationship

from datetime import datetime, timedelta

from core.database import Base

# ✅ ADD THIS
from models.Support.complaint_reply import ComplaintReply


class Complaint(Base):

    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)

    complaint_number = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    application_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    loan_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    category = Column(
        String,
        nullable=False,
        index=True
    )

    subject = Column(
        String,
        nullable=False
    )

    description = Column(
        Text,
        nullable=False
    )

    priority = Column(
        String,
        nullable=False,
        default="Medium"
    )

    status = Column(
        String,
        nullable=False,
        default="Open"
    )

    attachment_url = Column(
        String,
        nullable=True
    )

    escalated = Column(
        Boolean,
        default=False
    )

    resolution_notes = Column(
        Text,
        nullable=True
    )

    assigned_to = Column(
        String,
        nullable=True
    )

    sla_deadline = Column(
        DateTime,
        default=lambda:
            datetime.utcnow() + timedelta(days=30)
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user = relationship(
        "User",
        back_populates="complaints"
    )

    history = relationship(
        "ComplaintHistory",
        back_populates="complaint",
        cascade="all, delete-orphan"
    )

    # ✅ FIXED
    replies = relationship(
        "ComplaintReply",
        back_populates="complaint",
        cascade="all, delete-orphan"
    )