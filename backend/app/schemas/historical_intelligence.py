from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.exception import ExceptionCategory, ExceptionSeverity


class CurrentExceptionContext(BaseModel):
    category: ExceptionCategory
    severity: ExceptionSeverity
    financial_impact: Decimal | None
    priority_score: int

    model_config = ConfigDict(from_attributes=True)


class HistoricalExceptionContext(BaseModel):
    historical_transaction_count: int
    historical_exception_count: int
    same_category_exception_count: int
    recurrence_detected: bool


class HistoricalExceptionIntelligenceResponse(BaseModel):
    payment_id: str
    current_exception: CurrentExceptionContext | None
    historical_context: HistoricalExceptionContext