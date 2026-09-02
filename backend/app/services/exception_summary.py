from decimal import Decimal

from sqlalchemy.orm import Session

from app.schemas.exception_overview import ExceptionSummary
from app.services.exception_overview import get_exception_overview
from app.models.transaction import Transaction

def get_exception_summary(db: Session) -> ExceptionSummary:
    assessments = get_exception_overview(db)
    total_transactions = db.query(Transaction).count()

    category_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    financial_impact_by_category: dict[str, Decimal] = {}

    total_known_financial_impact = Decimal("0")

    for assessment in assessments:
        category = assessment.category.value
        severity = assessment.severity.value

        category_counts[category] = category_counts.get(category, 0) + 1
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

        if assessment.financial_impact is not None:
            total_known_financial_impact += assessment.financial_impact

            financial_impact_by_category[category] = (
                financial_impact_by_category.get(category, Decimal("0"))
                + assessment.financial_impact
            )
    
    dominant_exception_category = (
        max(
            category_counts,
            key=lambda category: category_counts[category],
        )
        if category_counts
        else None
    )

    high_priority_count = sum(
        1
        for assessment in assessments
        if assessment.priority_score >= 75
    )

    highest_priority_score = max(
        (assessment.priority_score for assessment in assessments),
        default=0,
    )

    exception_rate = (
        Decimal(len(assessments)) / Decimal(total_transactions) * Decimal("100")
        if total_transactions > 0
        else Decimal("0")
    )

    return ExceptionSummary(
        total_exceptions=len(assessments),
        total_transactions=total_transactions,
        exception_rate=exception_rate,
        total_known_financial_impact=total_known_financial_impact,
        financial_impact_by_category=financial_impact_by_category,
        category_counts=category_counts,
        severity_counts=severity_counts,
        high_priority_count=high_priority_count,
        highest_priority_score=highest_priority_score,
        dominant_exception_category=dominant_exception_category,
    )