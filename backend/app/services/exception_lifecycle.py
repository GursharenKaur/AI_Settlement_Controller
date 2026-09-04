from sqlalchemy.orm import Session

from app.models.controlled_action import ControlledAction
from app.models.exception import ExceptionRecord


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