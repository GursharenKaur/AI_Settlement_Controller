from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.settlement import Settlement
from app.models.transaction import Transaction
from app.schemas.reconciliation import (
    DriftDirection,
    ReconciliationResult,
    ReconciliationStatus,
)


def reconcile_transaction(
    transaction: Transaction,
    settlement: Settlement | None,
) -> ReconciliationResult:
    """
    Reconcile a transaction against its corresponding settlement.

    This function contains only deterministic reconciliation logic.
    Database access and HTTP concerns remain outside this function.
    """

    expected_amount = transaction.amount

    if settlement is None:
        return ReconciliationResult(
            payment_id=transaction.payment_id,
            status=ReconciliationStatus.MISSING_SETTLEMENT,
            expected_amount=expected_amount,
            actual_settled_amount=None,
            drift=expected_amount,
            drift_direction=DriftDirection.UNDER_SETTLED,
            transaction_currency=transaction.currency,
            settlement_currency=None,
        )

    if transaction.currency != settlement.currency:
        return ReconciliationResult(
            payment_id=transaction.payment_id,
            status=ReconciliationStatus.CURRENCY_MISMATCH,
            expected_amount=expected_amount,
            actual_settled_amount=settlement.settled_amount,
            drift=None,
            drift_direction=DriftDirection.NONE,
            transaction_currency=transaction.currency,
            settlement_currency=settlement.currency,
        )

    actual_amount = settlement.settled_amount

    if actual_amount == expected_amount:
        return ReconciliationResult(
            payment_id=transaction.payment_id,
            status=ReconciliationStatus.MATCHED,
            expected_amount=expected_amount,
            actual_settled_amount=actual_amount,
            drift=Decimal("0.00"),
            drift_direction=DriftDirection.NONE,
            transaction_currency=transaction.currency,
            settlement_currency=settlement.currency,
        )

    if actual_amount < expected_amount:
        return ReconciliationResult(
            payment_id=transaction.payment_id,
            status=ReconciliationStatus.AMOUNT_MISMATCH,
            expected_amount=expected_amount,
            actual_settled_amount=actual_amount,
            drift=expected_amount - actual_amount,
            drift_direction=DriftDirection.UNDER_SETTLED,
            transaction_currency=transaction.currency,
            settlement_currency=settlement.currency,
        )

    return ReconciliationResult(
        payment_id=transaction.payment_id,
        status=ReconciliationStatus.AMOUNT_MISMATCH,
        expected_amount=expected_amount,
        actual_settled_amount=actual_amount,
        drift=actual_amount - expected_amount,
        drift_direction=DriftDirection.OVER_SETTLED,
        transaction_currency=transaction.currency,
        settlement_currency=settlement.currency,
    )

def reconcile_payment(
    db: Session,
    payment_id: str,
) -> ReconciliationResult | None:
    """
    Load a transaction and its settlement from the database,
    then perform deterministic reconciliation.

    Returns None when the transaction does not exist.
    """

    transaction = (
        db.query(Transaction)
        .filter(Transaction.payment_id == payment_id)
        .first()
    )

    if transaction is None:
        return None

    settlement = (
        db.query(Settlement)
        .filter(Settlement.payment_id == payment_id)
        .order_by(Settlement.id)
        .first()
    )

    return reconcile_transaction(
        transaction=transaction,
        settlement=settlement,
    )