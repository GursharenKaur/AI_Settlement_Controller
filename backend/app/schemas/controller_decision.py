from decimal import Decimal
from enum import Enum

from pydantic import BaseModel

from app.models.exception import ExceptionLifecycleStatus
from app.schemas.exception import ExceptionCategory


class ControllerAction(str, Enum):
    INVESTIGATE_MISSING_SETTLEMENT = "INVESTIGATE_MISSING_SETTLEMENT"
    REVIEW_SETTLEMENT_AMOUNT = "REVIEW_SETTLEMENT_AMOUNT"
    REVIEW_CURRENCY_MISMATCH = "REVIEW_CURRENCY_MISMATCH"
    INVESTIGATE_INVALID_STATE = "INVESTIGATE_INVALID_STATE"
    NO_FURTHER_ACTION = "NO_FURTHER_ACTION"


class ControllerDecision(BaseModel):
    payment_id: str
    exception_category: ExceptionCategory
    lifecycle_status: ExceptionLifecycleStatus | None
    financial_impact: Decimal | None
    priority_score: int
    recommended_action: ControllerAction
    decision_reason: str
    human_review_required: bool