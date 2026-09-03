import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ControlledActionType(str, enum.Enum):
    INVESTIGATE_MISSING_SETTLEMENT = "INVESTIGATE_MISSING_SETTLEMENT"
    REVIEW_SETTLEMENT_AMOUNT = "REVIEW_SETTLEMENT_AMOUNT"
    REVIEW_CURRENCY_MISMATCH = "REVIEW_CURRENCY_MISMATCH"
    INVESTIGATE_INVALID_STATE = "INVESTIGATE_INVALID_STATE"


class ControlledActionStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class ControlledAction(Base):
    __tablename__ = "controlled_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    payment_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("transactions.payment_id"),
        nullable=False,
        index=True,
    )

    action_type: Mapped[ControlledActionType] = mapped_column(
        Enum(ControlledActionType),
        nullable=False,
    )

    status: Mapped[ControlledActionStatus] = mapped_column(
        Enum(ControlledActionStatus),
        nullable=False,
        default=ControlledActionStatus.REQUESTED,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )