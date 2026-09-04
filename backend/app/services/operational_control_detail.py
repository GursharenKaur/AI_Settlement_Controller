from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.controlled_action import ControlledAction
from app.models.exception import ExceptionRecord
from app.schemas.operational_control_detail import (
    OperationalControlAction,
    OperationalControlAuditEvent,
    OperationalControlDetail,
)
from app.services.controller_decision import build_controller_decision
from app.services.exception_intelligence import assess_exception
from app.services.reconciliation import reconcile_payment
from app.services.exception_aging import calculate_exception_age

def get_operational_control_detail(
    db: Session,
    payment_id: str,
) -> OperationalControlDetail | None:
    """
    Build the complete operational control detail for one exception.

    This function is read-only.

    It does not:
    - modify financial records,
    - execute controlled actions,
    - change lifecycle state,
    - create audit events,
    - or call AI.
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
            ExceptionRecord.payment_id == payment_id
        )
        .first()
    )

    assessment.lifecycle_status = (
        lifecycle_record.status
        if lifecycle_record is not None
        else None
    )

    if lifecycle_record is not None:
        age_minutes, age_hours, aging_band = calculate_exception_age(
            created_at=lifecycle_record.created_at,
        )
    else:
        age_minutes = None
        age_hours = None
        aging_band = None

    decision = build_controller_decision(assessment)

    controlled_actions = (
        db.query(ControlledAction)
        .filter(
            ControlledAction.payment_id == payment_id
        )
        .order_by(ControlledAction.id.asc())
        .all()
    )

    action_items = [
        OperationalControlAction.model_validate(action)
        for action in controlled_actions
    ]

    audit_logs = (
        db.query(AuditLog)
        .filter(
            AuditLog.payment_id == payment_id
        )
        .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
        .all()
    )

    audit_items = [
        OperationalControlAuditEvent.model_validate(event)
        for event in audit_logs
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

    return OperationalControlDetail(
        payment_id=assessment.payment_id,
        category=assessment.category,
        severity=assessment.severity,
        financial_impact=assessment.financial_impact,
        priority_score=assessment.priority_score,
        age_minutes=age_minutes,
        age_hours=age_hours,
        aging_band=aging_band,
        lifecycle_status=assessment.lifecycle_status,
        recommended_action=decision.recommended_action,
        human_review_required=decision.human_review_required,
        controlled_actions=action_items,
        audit_events=audit_items,
        remediation_status=remediation_status,
    )