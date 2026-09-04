from decimal import Decimal

from pydantic import BaseModel

from app.models.exception import ExceptionLifecycleStatus
from app.schemas.controller_decision import ControllerAction
from app.schemas.exception import ExceptionCategory, ExceptionSeverity
from app.schemas.governance import GovernanceClassificationResponse

class OperationalRiskItem(BaseModel):
    payment_id: str
    category: ExceptionCategory
    severity: ExceptionSeverity
    financial_impact: Decimal | None
    priority_score: int
    age_minutes: int | None
    age_hours: float | None
    aging_band: str | None
    lifecycle_status: ExceptionLifecycleStatus | None
    recommended_action: ControllerAction
    human_review_required: bool
    remediation_status: str
    attention_status: str
    governance: GovernanceClassificationResponse

class OperationalRiskSummary(BaseModel):
    total_exceptions: int
    action_required_count: int
    in_progress_count: int
    human_resolution_required_count: int
    monitor_count: int
    no_action_required_count: int
    total_known_financial_impact: Decimal
    highest_priority_payment_id: str | None
    highest_priority_score: int | None
    highest_priority_financial_impact: Decimal | None