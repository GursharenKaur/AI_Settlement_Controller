from decimal import Decimal

from pydantic import BaseModel

from app.models.exception import ExceptionLifecycleStatus
from app.schemas.controller_decision import ControllerAction
from app.schemas.exception import ExceptionCategory, ExceptionSeverity


class OperationalRiskItem(BaseModel):
    payment_id: str
    category: ExceptionCategory
    severity: ExceptionSeverity
    financial_impact: Decimal | None
    priority_score: int
    lifecycle_status: ExceptionLifecycleStatus | None
    recommended_action: ControllerAction
    human_review_required: bool
    remediation_status: str