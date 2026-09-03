from sqlalchemy.orm import Session

from app.models.exception import ExceptionRecord
from app.schemas.operational_control import (
    OperationalControlledAction,
    OperationalExceptionControl,
)
from app.services.controller_decision import build_controller_decision
from app.services.exception_intelligence import assess_exception
from app.services.exception_lifecycle import (
    get_controlled_actions_for_exception,
)
from app.services.reconciliation import reconcile_payment


def get_operational_exception_control(
    db: Session,
    payment_id: str,
) -> OperationalExceptionControl | None:
    """
    Build a deterministic operational control view for one payment.

    This function aggregates trusted system state. It does not:
    - modify financial records,
    - execute controlled actions,
    - resolve exceptions,
    - call the AI layer,
    - or create audit events.
    """

    reconciliation_result = reconcile_payment(
        db=db,
        payment_id=payment_id,
    )

    if reconciliation_result is None:
        return None

    assessment = assess_exception(reconciliation_result)

    if not assessment.is_exception:
        return None

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

    controlled_actions = get_controlled_actions_for_exception(
        db=db,
        payment_id=payment_id,
    )

    action_items = [
        OperationalControlledAction.model_validate(action)
        for action in controlled_actions
    ]

    if not controlled_actions:
        remediation_status = "NOT_STARTED"
    elif any(
        action.status.value == "IN_PROGRESS"
        for action in controlled_actions
    ):
        remediation_status = "IN_PROGRESS"
    elif any(
        action.status.value == "COMPLETED"
        for action in controlled_actions
    ):
        remediation_status = "COMPLETED"
    elif any(
        action.status.value == "FAILED"
        for action in controlled_actions
    ):
        remediation_status = "FAILED"
    elif any(
        action.status.value == "REJECTED"
        for action in controlled_actions
    ):
        remediation_status = "REJECTED"
    else:
        remediation_status = "REQUESTED"

    return OperationalExceptionControl(
        payment_id=assessment.payment_id,
        category=assessment.category,
        severity=assessment.severity,
        financial_impact=assessment.financial_impact,
        priority_score=assessment.priority_score,
        lifecycle_status=assessment.lifecycle_status,
        recommended_action=decision.recommended_action,
        human_review_required=decision.human_review_required,
        controlled_actions=action_items,
        remediation_status=remediation_status,
    )


def get_operational_exception_controls(
    db: Session,
) -> list[OperationalExceptionControl]:
    """
    Build operational control views for all current exceptions.

    Results remain deterministic and are ordered by priority.
    """

    from app.services.exception_overview import get_exception_overview

    assessments = get_exception_overview(db)

    controls: list[OperationalExceptionControl] = []

    for assessment in assessments:
        control = get_operational_exception_control(
            db=db,
            payment_id=assessment.payment_id,
        )

        if control is not None:
            controls.append(control)

    controls.sort(
        key=lambda control: control.priority_score,
        reverse=True,
    )

    return controls
