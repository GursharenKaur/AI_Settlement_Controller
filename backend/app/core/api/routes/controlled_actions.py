from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.controlled_action import ControlledAction
from app.models.exception import ExceptionRecord
from app.schemas.controlled_action import (
    ControlledActionCreate,
    ControlledActionResponse,
)
from app.schemas.controller_decision import ControllerAction
from app.services.controlled_action_validation import (
    validate_controller_action,
)
from app.services.controller_decision import build_controller_decision
from app.services.exception_intelligence import assess_exception
from app.services.reconciliation import reconcile_payment

from app.services.controlled_action_execution import (
    start_controlled_action,
    complete_controlled_action,
)

from app.models.audit_log import AuditEventType
from app.services.audit_log import create_audit_log

router = APIRouter(
    prefix="/controlled-actions",
    tags=["Controlled Actions"],
)


@router.post(
    "",
    response_model=ControlledActionResponse,
)
def create_controlled_action(
    request: ControlledActionCreate,
    db: Session = Depends(get_db),
):
    reconciliation_result = reconcile_payment(
        db=db,
        payment_id=request.payment_id,
    )

    if reconciliation_result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Payment {request.payment_id} not found",
        )

    assessment = assess_exception(reconciliation_result)

    lifecycle_record = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.payment_id == assessment.payment_id
        )
        .first()
    )

    assessment.lifecycle_status = (
        lifecycle_record.status
        if lifecycle_record is not None
        else None
    )

    decision = build_controller_decision(assessment)

    requested_action = ControllerAction(request.action_type.value)

    is_valid, validation_reason = validate_controller_action(
        decision,
        requested_action,
    )

    if not is_valid:
        create_audit_log(
            db=db,
            payment_id=request.payment_id,
            event_type=AuditEventType.CONTROLLED_ACTION_REJECTED,
            message=(
                f"Controlled action request rejected for action type "
                f"'{requested_action.value}': {validation_reason}"
            ),
        )

        raise HTTPException(
            status_code=400,
            detail=validation_reason,
        )

    controlled_action = ControlledAction(
        payment_id=request.payment_id,
        action_type=request.action_type,
        reason=decision.decision_reason,
    )

    db.add(controlled_action)
    db.commit()
    db.refresh(controlled_action)

    create_audit_log(
        db=db,
        payment_id=controlled_action.payment_id,
        controlled_action_id=controlled_action.id,
        event_type=AuditEventType.CONTROLLED_ACTION_CREATED,
        message=(
            f"Controlled action {controlled_action.id} created for "
            f"action type '{controlled_action.action_type.value}'."
        ),
    )

    return controlled_action

@router.post(
    "/{action_id}/execute",
    response_model=ControlledActionResponse,
)
def execute_controlled_action(
    action_id: int,
    db: Session = Depends(get_db),
):
    controlled_action = (
        db.query(ControlledAction)
        .filter(ControlledAction.id == action_id)
        .first()
    )

    if controlled_action is None:
        raise HTTPException(
            status_code=404,
            detail=f"Controlled action {action_id} not found",
        )

    try:
        start_controlled_action(
            db=db,
            action=controlled_action,
        )

        complete_controlled_action(
            db=db,
            action=controlled_action,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return controlled_action