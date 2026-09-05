from sqlalchemy.orm import Session

from app.models.controlled_action import ControlledAction
from app.models.exception import ExceptionRecord, ExceptionLifecycleStatus
from app.models.settlement import Settlement
from app.models.transaction import Transaction
from app.services.exception_intelligence import assess_exception
from app.services.reconciliation import reconcile_transaction


def get_exception_record(
    db: Session,
    payment_id: str,
) -> ExceptionRecord | None:
    """
    Return the persisted lifecycle record for an exception.

    This function is read-only.

    If no lifecycle record exists, None is returned.
    No lifecycle record is created implicitly.
    """

    return (
        db.query(ExceptionRecord)
        .filter(ExceptionRecord.payment_id == payment_id)
        .first()
    )


def ensure_exception_lifecycle(
    db: Session,
    payment_id: str,
) -> ExceptionRecord | None:
    """
    Materialize an OPEN lifecycle record when the current
    deterministic assessment confirms that a payment is an exception.

    This is an explicit write-path helper. It must only be called from
    transaction/settlement write operations, never from read-only
    projection endpoints.

    Existing lifecycle records are preserved and never reset implicitly.
    Matched payments do not receive a lifecycle record.
    """

    existing = get_exception_record(
        db=db,
        payment_id=payment_id,
    )

    if existing is not None:
        return existing

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

    reconciliation_result = reconcile_transaction(
        transaction=transaction,
        settlement=settlement,
    )

    assessment = assess_exception(reconciliation_result)

    if not assessment.is_exception:
        return None

    record = ExceptionRecord(
        payment_id=payment_id,
        status=ExceptionLifecycleStatus.OPEN,
    )

    db.add(record)

    return record


def get_controlled_actions_for_exception(
    db: Session,
    payment_id: str,
) -> list[ControlledAction]:
    """
    Return all controlled remediation actions associated
    with the exception's payment.
    """

    return (
        db.query(ControlledAction)
        .filter(ControlledAction.payment_id == payment_id)
        .order_by(ControlledAction.id)
        .all()
    )