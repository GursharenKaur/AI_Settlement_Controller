from decimal import Decimal
from app.schemas.exception import (
    ExceptionAssessment,
    ExceptionCategory,
    ExceptionSeverity,
)
from app.schemas.reconciliation import (
    DriftDirection,
    ReconciliationStatus,
    ReconciliationResult,
)


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
        )

    if result.status == ReconciliationStatus.MISSING_SETTLEMENT:
        return ExceptionAssessment(
            payment_id=result.payment_id,
            is_exception=True,
            category=ExceptionCategory.MISSING_SETTLEMENT,
            severity=ExceptionSeverity.HIGH,
            financial_impact=result.drift,
        )

    if result.status == ReconciliationStatus.CURRENCY_MISMATCH:
        return ExceptionAssessment(
            payment_id=result.payment_id,
            is_exception=True,
            category=ExceptionCategory.CURRENCY_MISMATCH,
            severity=ExceptionSeverity.HIGH,
            financial_impact=None,
        )

    if result.status == ReconciliationStatus.INVALID_STATE:
        return ExceptionAssessment(
            payment_id=result.payment_id,
            is_exception=True,
            category=ExceptionCategory.INVALID_STATE,
            severity=ExceptionSeverity.HIGH,
            financial_impact=None,
        )

    if result.status == ReconciliationStatus.AMOUNT_MISMATCH:
        if result.drift_direction == DriftDirection.UNDER_SETTLED:
            return ExceptionAssessment(
                payment_id=result.payment_id,
                is_exception=True,
                category=ExceptionCategory.UNDER_SETTLEMENT,
                severity=ExceptionSeverity.MEDIUM,
                financial_impact=result.drift,
            )

        if result.drift_direction == DriftDirection.OVER_SETTLED:
            return ExceptionAssessment(
                payment_id=result.payment_id,
                is_exception=True,
                category=ExceptionCategory.OVER_SETTLEMENT,
                severity=ExceptionSeverity.HIGH,
                financial_impact=result.drift,
            )

    raise ValueError(
        f"Unsupported reconciliation result for payment "
        f"{result.payment_id}"
    )