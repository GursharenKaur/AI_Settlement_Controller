from decimal import Decimal

from pydantic import BaseModel

from app.schemas.exception import ExceptionCategory, ExceptionSeverity


class ExceptionAIContext(BaseModel):
    payment_id: str
    exception_category: ExceptionCategory
    severity: ExceptionSeverity
    financial_impact: Decimal | None
    priority_score: int
    overall_risk_band: str
    overall_financial_risk_level: str