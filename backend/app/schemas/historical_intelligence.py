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
    same_currency_exception_count: int
    same_category_and_currency_exception_count: int
    recurrence_detected: bool
    timing_available: bool
    settlement_delay_hours: float | None
    historical_settlement_count: int
    historical_average_delay_hours: float | None
    timing_deviation_hours: float | None

class HistoricalExceptionIntelligenceResponse(BaseModel):
    payment_id: str
    current_exception: CurrentExceptionContext | None
    historical_context: HistoricalExceptionContext