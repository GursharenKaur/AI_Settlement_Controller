from sqlalchemy.orm import Session

from app.models.audit_log import AuditEventType, AuditLog


def create_audit_log(
    db: Session,
    payment_id: str,
    event_type: AuditEventType,
    message: str,
    controlled_action_id: int | None = None,
    previous_status: str | None = None,
    new_status: str | None = None,
) -> AuditLog:
    """
    Create and persist an immutable operational audit event.

    State-transition evidence is recorded when applicable.
    The audit log does not modify financial records or control state.
    """

    audit_log = AuditLog(
        payment_id=payment_id,
        controlled_action_id=controlled_action_id,
        event_type=event_type,
        message=message,
        previous_status=previous_status,
        new_status=new_status,
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log