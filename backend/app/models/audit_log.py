import enum

from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditEventType(str, enum.Enum):
    CONTROLLED_ACTION_CREATED = "CONTROLLED_ACTION_CREATED"
    CONTROLLED_ACTION_STARTED = "CONTROLLED_ACTION_STARTED"
    CONTROLLED_ACTION_COMPLETED = "CONTROLLED_ACTION_COMPLETED"
    CONTROLLED_ACTION_FAILED = "CONTROLLED_ACTION_FAILED"
    CONTROLLED_ACTION_REJECTED = "CONTROLLED_ACTION_REJECTED"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    payment_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    controlled_action_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )