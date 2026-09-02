from decimal import Decimal

from pydantic import BaseModel


class PortfolioAIContext(BaseModel):
    total_transactions: int
    total_exceptions: int
    exception_rate: Decimal
    total_known_financial_impact: Decimal
    financial_impact_rate: Decimal
    financial_impact_by_category: dict[str, Decimal]
    category_counts: dict[str, int]
    severity_counts: dict[str, int]
    high_priority_count: int
    highest_priority_score: int
    dominant_exception_category: str | None
    overall_risk_band: str
    overall_financial_risk_level: str