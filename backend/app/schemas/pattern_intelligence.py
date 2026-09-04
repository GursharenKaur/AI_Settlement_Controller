from decimal import Decimal

from pydantic import BaseModel

from app.schemas.exception import ExceptionCategory


class ExceptionPattern(BaseModel):
    category: ExceptionCategory
    exception_count: int
    high_severity_count: int
    known_financial_impact_by_currency: dict[str, Decimal]


class PatternIntelligenceResponse(BaseModel):
    total_transactions: int
    total_exceptions: int
    categories: list[ExceptionPattern]
    recurring_categories: list[ExceptionCategory]