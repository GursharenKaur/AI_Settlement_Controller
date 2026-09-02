from decimal import Decimal

from pydantic import BaseModel


class ExceptionSummary(BaseModel):
    total_exceptions: int
    total_transactions: int
    exception_rate: Decimal
    total_known_financial_impact: Decimal
    financial_impact_rate: Decimal
    financial_impact_by_category: dict[str, Decimal]
    category_counts: dict[str, int]
    severity_counts: dict[str, int]
    high_priority_count: int
    highest_priority_score: int
    dominant_exception_category: str | None
    risk_band: str
    financial_risk_level: str