from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.exception import ExceptionLifecycleStatus
from app.models.transaction import Transaction
from app.schemas.exception_overview import ExceptionSummary
from app.services.exception_overview import get_exception_overview


def get_exception_summary(db: Session) -> ExceptionSummary:
    assessments = get_exception_overview(db)

    total_transactions = db.query(Transaction).count()

    total_transaction_amount = (
        db.query(Transaction)
        .with_entities(Transaction.amount)
        .all()
    )

    total_transaction_amount = sum(
        (amount for (amount,) in total_transaction_amount),
        Decimal("0"),
    )

    category_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    financial_impact_by_category: dict[str, Decimal] = {}

    total_known_financial_impact = Decimal("0")

    open_exception_count = 0
    acknowledged_exception_count = 0
    resolved_exception_count = 0

    for assessment in assessments:
        category = assessment.category.value
        severity = assessment.severity.value

        category_counts[category] = category_counts.get(category, 0) + 1
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

        if assessment.lifecycle_status == ExceptionLifecycleStatus.OPEN:
            open_exception_count += 1
        elif (
            assessment.lifecycle_status
            == ExceptionLifecycleStatus.ACKNOWLEDGED
        ):
            acknowledged_exception_count += 1
        elif (
            assessment.lifecycle_status
            == ExceptionLifecycleStatus.RESOLVED
        ):
            resolved_exception_count += 1

        if assessment.financial_impact is not None:
            total_known_financial_impact += assessment.financial_impact

            financial_impact_by_category[category] = (
                financial_impact_by_category.get(
                    category,
                    Decimal("0"),
                )
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

    if highest_priority_score >= 90:
        risk_band = "CRITICAL"
    elif highest_priority_score >= 75:
        risk_band = "HIGH"
    elif highest_priority_score >= 50:
        risk_band = "MEDIUM"
    else:
        risk_band = "LOW"

    if total_known_financial_impact >= Decimal("50000"):
        financial_risk_level = "CRITICAL"
    elif total_known_financial_impact >= Decimal("10000"):
        financial_risk_level = "HIGH"
    elif total_known_financial_impact > Decimal("0"):
        financial_risk_level = "LOW"
    else:
        financial_risk_level = "NONE"

    exception_rate = (
        Decimal(len(assessments))
        / Decimal(total_transactions)
        * Decimal("100")
        if total_transactions > 0
        else Decimal("0")
    )

    financial_impact_rate = (
        total_known_financial_impact
        / total_transaction_amount
        * Decimal("100")
        if total_transaction_amount > 0
        else Decimal("0")
    )

    return ExceptionSummary(
        total_exceptions=len(assessments),
        open_exception_count=open_exception_count,
        acknowledged_exception_count=acknowledged_exception_count,
        resolved_exception_count=resolved_exception_count,
        total_transactions=total_transactions,
        exception_rate=exception_rate,
        total_known_financial_impact=total_known_financial_impact,
        financial_impact_rate=financial_impact_rate,
        financial_impact_by_category=financial_impact_by_category,
        category_counts=category_counts,
        severity_counts=severity_counts,
        high_priority_count=high_priority_count,
        highest_priority_score=highest_priority_score,
        dominant_exception_category=dominant_exception_category,
        risk_band=risk_band,
        financial_risk_level=financial_risk_level,
    )