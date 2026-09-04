from sqlalchemy.orm import Session

from app.models.settlement import Settlement
from app.models.transaction import Transaction
from app.schemas.exception import ExceptionAssessment
from app.services.exception_intelligence import assess_exception
from app.services.reconciliation import reconcile_transaction


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
                "recurrence_detected": False,
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

    historical_transactions = [
        transaction
        for transaction in transactions
        if str(transaction.payment_id) != str(payment_id)
    ]

    historical_assessments: list[ExceptionAssessment] = []

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
            historical_assessments.append(assessment)

    same_category_exception_count = 0

    if current_assessment.is_exception:
        same_category_exception_count = sum(
            1
            for assessment in historical_assessments
            if assessment.category == current_assessment.category
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
            "historical_exception_count": len(historical_assessments),
            "same_category_exception_count": same_category_exception_count,
            "recurrence_detected": recurrence_detected,
        },
    }