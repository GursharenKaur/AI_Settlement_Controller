from decimal import Decimal

from app.schemas.exception import (
    ExceptionAssessment,
    ExceptionCategory,
    ExceptionSeverity,
)
from app.schemas.reconciliation import (
    DriftDirection,
    ReconciliationResult,
    ReconciliationStatus,
)


def calculate_priority_score(
    severity: ExceptionSeverity,
    financial_impact: Decimal | None,
) -> int:
    """
    Calculate a deterministic priority score for an exception.

    Severity provides the base score, while larger known
    financial impacts increase the priority.

    Maximum score is 100.
    """

    severity_scores = {
        ExceptionSeverity.NONE: 0,
        ExceptionSeverity.LOW: 25,
        ExceptionSeverity.MEDIUM: 50,
        ExceptionSeverity.HIGH: 75,
    }

    score = severity_scores[severity]

    if financial_impact is not None:
        if financial_impact >= Decimal("10000"):
            score += 25
        elif financial_impact >= Decimal("1000"):
            score += 10

    return min(score, 100)


def assess_exception(
    result: ReconciliationResult,
) -> ExceptionAssessment:
    """
    Convert a deterministic reconciliation result into
    an operational exception assessment.

    This layer does not perform reconciliation.
    It interprets the already-established financial result.
    """

    if result.status == ReconciliationStatus.MATCHED:
        return ExceptionAssessment(
            payment_id=result.payment_id,
            is_exception=False,
            category=ExceptionCategory.NONE,
            severity=ExceptionSeverity.NONE,
            financial_impact=Decimal("0"),
            priority_score=calculate_priority_score(
                severity=ExceptionSeverity.NONE,
                financial_impact=Decimal("0"),
            ),
        )

    if result.status == ReconciliationStatus.MISSING_SETTLEMENT:
        return ExceptionAssessment(
            payment_id=result.payment_id,
            is_exception=True,
            category=ExceptionCategory.MISSING_SETTLEMENT,
            severity=ExceptionSeverity.HIGH,
            financial_impact=result.drift,
            priority_score=calculate_priority_score(
                severity=ExceptionSeverity.HIGH,
                financial_impact=result.drift,
            ),
        )

    if result.status == ReconciliationStatus.CURRENCY_MISMATCH:
        return ExceptionAssessment(
            payment_id=result.payment_id,
            is_exception=True,
            category=ExceptionCategory.CURRENCY_MISMATCH,
            severity=ExceptionSeverity.HIGH,
            financial_impact=None,
            priority_score=calculate_priority_score(
                severity=ExceptionSeverity.HIGH,
                financial_impact=None,
            ),
        )

    if result.status == ReconciliationStatus.INVALID_STATE:
        return ExceptionAssessment(
            payment_id=result.payment_id,
            is_exception=True,
            category=ExceptionCategory.INVALID_STATE,
            severity=ExceptionSeverity.HIGH,
            financial_impact=None,
            priority_score=calculate_priority_score(
                severity=ExceptionSeverity.HIGH,
                financial_impact=None,
            ),
        )

    if result.status == ReconciliationStatus.AMOUNT_MISMATCH:
        if result.drift_direction == DriftDirection.UNDER_SETTLED:
            return ExceptionAssessment(
                payment_id=result.payment_id,
                is_exception=True,
                category=ExceptionCategory.UNDER_SETTLEMENT,
                severity=ExceptionSeverity.MEDIUM,
                financial_impact=result.drift,
                priority_score=calculate_priority_score(
                    severity=ExceptionSeverity.MEDIUM,
                    financial_impact=result.drift,
                ),
            )

        if result.drift_direction == DriftDirection.OVER_SETTLED:
            return ExceptionAssessment(
                payment_id=result.payment_id,
                is_exception=True,
                category=ExceptionCategory.OVER_SETTLEMENT,
                severity=ExceptionSeverity.HIGH,
                financial_impact=result.drift,
                priority_score=calculate_priority_score(
                    severity=ExceptionSeverity.HIGH,
                    financial_impact=result.drift,
                ),
            )

    raise ValueError(
        f"Unsupported reconciliation result for payment "
        f"{result.payment_id}"
    )
