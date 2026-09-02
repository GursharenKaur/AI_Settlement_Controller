from app.schemas.ai_portfolio_context import PortfolioAIContext
from app.schemas.exception_overview import ExceptionSummary


def build_portfolio_ai_context(
    summary: ExceptionSummary,
) -> PortfolioAIContext:
    """
    Build trusted portfolio-level context for AI analysis.

    All financial and risk metrics come from the deterministic
    exception summary. This function does not perform AI reasoning.
    """

    return PortfolioAIContext(
        total_transactions=summary.total_transactions,
        total_exceptions=summary.total_exceptions,
        exception_rate=summary.exception_rate,
        total_known_financial_impact=summary.total_known_financial_impact,
        financial_impact_rate=summary.financial_impact_rate,
        financial_impact_by_category=summary.financial_impact_by_category,
        category_counts=summary.category_counts,
        severity_counts=summary.severity_counts,
        high_priority_count=summary.high_priority_count,
        highest_priority_score=summary.highest_priority_score,
        dominant_exception_category=summary.dominant_exception_category,
        overall_risk_band=summary.risk_band,
        overall_financial_risk_level=summary.financial_risk_level,
    )