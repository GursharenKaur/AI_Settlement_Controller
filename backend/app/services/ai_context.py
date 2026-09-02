from app.schemas.ai_context import ExceptionAIContext
from app.schemas.exception import ExceptionAssessment
from app.schemas.exception_overview import ExceptionSummary


def build_exception_ai_context(
    assessment: ExceptionAssessment,
    summary: ExceptionSummary,
) -> ExceptionAIContext:
    """
    Build a trusted, structured context for future AI analysis.

    Exception-level facts come from the deterministic assessment.
    Overall risk signals come from the deterministic exception summary.
    This function does not perform AI reasoning.
    """

    return ExceptionAIContext(
        payment_id=assessment.payment_id,
        exception_category=assessment.category,
        severity=assessment.severity,
        financial_impact=assessment.financial_impact,
        priority_score=assessment.priority_score,
        overall_risk_band=summary.risk_band,
        overall_financial_risk_level=summary.financial_risk_level,
    )