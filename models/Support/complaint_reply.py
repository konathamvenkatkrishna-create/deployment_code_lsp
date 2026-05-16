from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Text,
    DateTime,
    String
)

from sqlalchemy.orm import relationship

from datetime import datetime

from core.database import Base


class ComplaintReply(Base):

    __tablename__ = "complaint_replies"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    complaint_id = Column(
        Integer,
        ForeignKey("complaints.id"),
        nullable=False,
        index=True
    )

    sender_type = Column(
        String(20),
        nullable=False
    )
    # USER / SUPPORT

    sender_id = Column(
        Integer,
        nullable=False
    )

    message = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    complaint = relationship(
        "Complaint",
        back_populates="replies"
    )