from sqlalchemy.orm import Session

from app.models.exception import (
    ExceptionLifecycleStatus,
    ExceptionRecord,
)


def get_or_create_exception_record(
    db: Session,
    payment_id: str,
) -> ExceptionRecord:
    """
    Get the persisted lifecycle record for an exception.

    If no record exists, create it with OPEN status.
    """

    record = (
        db.query(ExceptionRecord)
        .filter(ExceptionRecord.payment_id == payment_id)
        .first()
    )

    if record is not None:
        return record

    record = ExceptionRecord(
        payment_id=payment_id,
        status=ExceptionLifecycleStatus.OPEN,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record