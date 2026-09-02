from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class ExceptionCategory(str, Enum):
    NONE = "NONE"
    MISSING_SETTLEMENT = "MISSING_SETTLEMENT"
    UNDER_SETTLEMENT = "UNDER_SETTLEMENT"
    OVER_SETTLEMENT = "OVER_SETTLEMENT"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    INVALID_STATE = "INVALID_STATE"


class ExceptionSeverity(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ExceptionAssessment(BaseModel):
    payment_id: str
    is_exception: bool
    category: ExceptionCategory
    severity: ExceptionSeverity
    financial_impact: Decimal | None
    priority_score: int