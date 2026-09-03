from sqlalchemy.orm import Session

from app.models.audit_log import AuditEventType, AuditLog


def create_audit_log(
    db: Session,
    payment_id: str,
    event_type: AuditEventType,
    message: str,
    controlled_action_id: int | None = None,
) -> AuditLog:
    """
    Create and persist an immutable operational audit event.
    """

    audit_log = AuditLog(
        payment_id=payment_id,
        controlled_action_id=controlled_action_id,
        event_type=event_type,
        message=message,
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log