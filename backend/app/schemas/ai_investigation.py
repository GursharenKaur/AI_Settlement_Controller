from decimal import Decimal

from pydantic import BaseModel

from app.schemas.exception import ExceptionCategory, ExceptionSeverity


class AIInvestigationContext(BaseModel):
    payment_id: str

    exception_category: ExceptionCategory
    severity: ExceptionSeverity
    financial_impact: Decimal | None
    priority_score: int

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

    population_total_transactions: int
    population_total_exceptions: int
    recurring_categories: list[ExceptionCategory]


class AIInvestigationAnalysis(BaseModel):
    payment_id: str
    investigation_summary: str
    historical_context_explanation: str
    timing_context_explanation: str
    evidence_gaps: str
    investigation_guidance: str