from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.controlled_action import (
    ControlledActionStatus,
    ControlledActionType,
)
from app.models.exception import ExceptionLifecycleStatus
from app.schemas.controller_decision import ControllerAction
from app.schemas.exception import (
    ExceptionCategory,
    ExceptionSeverity,
)


class OperationalControlledAction(BaseModel):
    id: int
    action_type: ControlledActionType
    status: ControlledActionStatus
    result: str | None
    executed_at: datetime | None

    model_config = {
        "from_attributes": True,
    }


class OperationalExceptionControl(BaseModel):
    payment_id: str
    category: ExceptionCategory
    severity: ExceptionSeverity
    financial_impact: Decimal | None
    priority_score: int
    lifecycle_status: ExceptionLifecycleStatus | None
    recommended_action: ControllerAction
    human_review_required: bool
    controlled_actions: list[OperationalControlledAction]
    remediation_status: str
