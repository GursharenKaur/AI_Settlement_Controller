from datetime import datetime

from sqlalchemy.orm import Session

from app.models.audit_log import AuditEventType
from app.models.controlled_action import (
    ControlledAction,
    ControlledActionStatus,
)
from app.services.audit_log import create_audit_log


def start_controlled_action(
    db: Session,
    action: ControlledAction,
) -> ControlledAction:
    """
    Move a requested controlled action into execution.

    This function does not perform financial movement or modify
    transaction/settlement financial data.
    """

    if action.status != ControlledActionStatus.REQUESTED:
        raise ValueError(
            f"Controlled action {action.id} cannot start from "
            f"status '{action.status.value}'."
        )

    action.status = ControlledActionStatus.IN_PROGRESS

    db.commit()
    db.refresh(action)

    create_audit_log(
        db=db,
        payment_id=action.payment_id,
        controlled_action_id=action.id,
        event_type=AuditEventType.CONTROLLED_ACTION_STARTED,
        message=(
            f"Controlled action {action.id} started execution "
            f"for action type '{action.action_type.value}'."
        ),
    )

    return action


def complete_controlled_action(
    db: Session,
    action: ControlledAction,
) -> ControlledAction:
    """
    Complete a controlled action that is currently in progress.

    Records the execution result and completion timestamp without
    modifying financial records.
    """

    if action.status != ControlledActionStatus.IN_PROGRESS:
        raise ValueError(
            f"Controlled action {action.id} cannot complete from "
            f"status '{action.status.value}'."
        )

    action.status = ControlledActionStatus.COMPLETED
    action.result = "Controlled action completed successfully."
    action.executed_at = datetime.utcnow()

    db.commit()
    db.refresh(action)

    create_audit_log(
        db=db,
        payment_id=action.payment_id,
        controlled_action_id=action.id,
        event_type=AuditEventType.CONTROLLED_ACTION_COMPLETED,
        message=(
            f"Controlled action {action.id} completed successfully."
        ),
    )

    return action