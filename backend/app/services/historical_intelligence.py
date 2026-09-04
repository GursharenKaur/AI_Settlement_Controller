from datetime import datetime

from sqlalchemy.orm import Session

from app.models.settlement import Settlement
from app.models.transaction import Transaction
from app.schemas.exception import ExceptionAssessment
from app.services.exception_intelligence import assess_exception
from app.services.reconciliation import reconcile_transaction


def calculate_settlement_delay_hours(
    paid_at: datetime | None,
    settled_at: datetime | None,
) -> float | None:
    """
    Calculate settlement delay in hours.

    Returns None when either timestamp is unavailable.
    """
    if paid_at is None or settled_at is None:
        return None

    delay = settled_at - paid_at
    return delay.total_seconds() / 3600


def get_historical_exception_context(
    db: Session,
    payment_id: str,
) -> dict:
    """
    Derive historical exception evidence for a payment.

    Historical evidence is calculated from authoritative transaction
    and settlement data using the existing deterministic reconciliation
    and exception-assessment engines.

    This service is read-only:
    - does not mutate financial records
    - does not create or modify ExceptionRecord
    - does not create controlled actions
    - does not resolve exceptions
    - does not create audit events
    - does not invoke AI
    - does not modify priority or governance
    """

    transactions = (
        db.query(Transaction)
        .order_by(Transaction.id)
        .all()
    )

    settlements = (
        db.query(Settlement)
        .order_by(Settlement.id)
        .all()
    )

    settlements_by_payment_id: dict[str, Settlement] = {}

    for settlement in settlements:
        settlement_payment_id = str(settlement.payment_id)

        # Preserve existing reconciliation behavior:
        # the first settlement ordered by ID is authoritative.
        if settlement_payment_id not in settlements_by_payment_id:
            settlements_by_payment_id[settlement_payment_id] = settlement

    current_transaction = next(
        (
            transaction
            for transaction in transactions
            if str(transaction.payment_id) == str(payment_id)
        ),
        None,
    )

    if current_transaction is None:
        return {
            "payment_id": str(payment_id),
            "current_exception": None,
            "historical_context": {
                "historical_transaction_count": 0,
                "historical_exception_count": 0,
                "same_category_exception_count": 0,
                "same_currency_exception_count": 0,
                "same_category_and_currency_exception_count": 0,
                "recurrence_detected": False,
                "timing_available": False,
                "settlement_delay_hours": None,
                "historical_settlement_count": 0,
                "historical_average_delay_hours": None,
                "timing_deviation_hours": None,
            },
        }

    current_settlement = settlements_by_payment_id.get(
        str(current_transaction.payment_id)
    )

    current_reconciliation = reconcile_transaction(
        transaction=current_transaction,
        settlement=current_settlement,
    )

    current_assessment = assess_exception(current_reconciliation)

    current_settlement_delay_hours = calculate_settlement_delay_hours(
        paid_at=current_transaction.paid_at,
        settled_at=(
            current_settlement.settled_at
            if current_settlement is not None
            else None
        ),
    )

    timing_available = current_settlement_delay_hours is not None

    historical_transactions = [
        transaction
        for transaction in transactions
        if str(transaction.payment_id) != str(payment_id)
    ]

    historical_timing_delays: list[float] = []

    for transaction in historical_transactions:
        if transaction.currency != current_transaction.currency:
            continue

        settlement = settlements_by_payment_id.get(
            str(transaction.payment_id)
        )

        delay_hours = calculate_settlement_delay_hours(
            paid_at=transaction.paid_at,
            settled_at=(
                settlement.settled_at
                if settlement is not None
                else None
            ),
        )

        if delay_hours is not None:
            historical_timing_delays.append(delay_hours)

    historical_settlement_count = len(historical_timing_delays)

    historical_average_delay_hours = (
        sum(historical_timing_delays) / historical_settlement_count
        if historical_settlement_count > 0
        else None
    )

    timing_deviation_hours = (
        current_settlement_delay_hours - historical_average_delay_hours
        if (
            current_settlement_delay_hours is not None
            and historical_average_delay_hours is not None
        )
        else None
    )

    historical_exception_records: list[
        tuple[Transaction, ExceptionAssessment]
    ] = []

    for transaction in historical_transactions:
        settlement = settlements_by_payment_id.get(
            str(transaction.payment_id)
        )

        reconciliation_result = reconcile_transaction(
            transaction=transaction,
            settlement=settlement,
        )

        assessment = assess_exception(reconciliation_result)

        if assessment.is_exception:
            historical_exception_records.append(
                (transaction, assessment)
            )

    same_category_exception_count = 0
    same_currency_exception_count = 0
    same_category_and_currency_exception_count = 0

    if current_assessment.is_exception:
        same_category_exception_count = sum(
            1
            for _, assessment in historical_exception_records
            if assessment.category == current_assessment.category
        )

        same_currency_exception_count = sum(
            1
            for transaction, _ in historical_exception_records
            if transaction.currency == current_transaction.currency
        )

        same_category_and_currency_exception_count = sum(
            1
            for transaction, assessment in historical_exception_records
            if (
                assessment.category == current_assessment.category
                and transaction.currency == current_transaction.currency
            )
        )

    recurrence_detected = same_category_exception_count > 0

    return {
        "payment_id": str(payment_id),
        "current_exception": {
            "category": current_assessment.category,
            "severity": current_assessment.severity,
            "financial_impact": current_assessment.financial_impact,
            "priority_score": current_assessment.priority_score,
        },
        "historical_context": {
            "historical_transaction_count": len(historical_transactions),
            "historical_exception_count": len(historical_exception_records),
            "same_category_exception_count": same_category_exception_count,
            "same_currency_exception_count": same_currency_exception_count,
            "same_category_and_currency_exception_count": (
                same_category_and_currency_exception_count
            ),
            "recurrence_detected": recurrence_detected,
            "timing_available": timing_available,
            "settlement_delay_hours": current_settlement_delay_hours,
            "historical_settlement_count": historical_settlement_count,
            "historical_average_delay_hours": historical_average_delay_hours,
            "timing_deviation_hours": timing_deviation_hours,
        },
    }
