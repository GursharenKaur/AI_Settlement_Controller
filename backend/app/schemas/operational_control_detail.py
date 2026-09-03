from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.controlled_action import (
    ControlledActionStatus,
    ControlledActionType,
)
from app.models.exception import ExceptionLifecycleStatus
from app.models.audit_log import AuditEventType
from app.schemas.controller_decision import ControllerAction
from app.schemas.exception import (
    ExceptionCategory,
    ExceptionSeverity,
)


class OperationalControlAction(BaseModel):
    id: int
    action_type: ControlledActionType
    status: ControlledActionStatus
    reason: str
    result: str | None
    created_at: datetime
    updated_at: datetime
    executed_at: datetime | None

    model_config = {
        "from_attributes": True,
    }


class OperationalControlAuditEvent(BaseModel):
    id: int
    payment_id: str
    controlled_action_id: int | None
    event_type: AuditEventType
    message: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class OperationalControlDetail(BaseModel):
    payment_id: str

    category: ExceptionCategory
    severity: ExceptionSeverity
    financial_impact: Decimal | None
    priority_score: int

    lifecycle_status: ExceptionLifecycleStatus | None

    recommended_action: ControllerAction
    human_review_required: bool

    remediation_status: str

    controlled_actions: list[OperationalControlAction]
    audit_events: list[OperationalControlAuditEvent]