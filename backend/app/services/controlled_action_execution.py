from datetime import datetime

from sqlalchemy.orm import Session

from app.models.controlled_action import (
    ControlledAction,
    ControlledActionStatus,
)


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

    return action