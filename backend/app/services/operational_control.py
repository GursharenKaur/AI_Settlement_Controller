from sqlalchemy.orm import Session
from decimal import Decimal
from app.models.exception import ExceptionRecord
from app.schemas.operational_control import (
    OperationalControlledAction,
    OperationalExceptionControl,
    OperationalControlSummary,
)
from app.services.controller_decision import build_controller_decision
from app.services.exception_intelligence import assess_exception
from app.services.exception_lifecycle import (
    get_controlled_actions_for_exception,
)
from app.services.reconciliation import reconcile_payment
from decimal import Decimal
from app.services.exception_aging import calculate_exception_age

from app.services.governance import classify_governance
from app.schemas.governance import GovernanceClassificationResponse

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

    if lifecycle_record is not None:
        age_minutes, age_hours, aging_band = calculate_exception_age(
            created_at=lifecycle_record.created_at,
        )
    else:
        age_minutes = None
        age_hours = None
        aging_band = None

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
    
    governance = classify_governance(
        lifecycle_status=assessment.lifecycle_status,
        remediation_status=remediation_status,
        aging_band=aging_band,
        priority_score=assessment.priority_score,
        human_review_required=decision.human_review_required,
    )
    
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
        age_minutes=age_minutes,
        age_hours=age_hours,
        aging_band=aging_band,
        governance=GovernanceClassificationResponse(
            governance_level=governance.governance_level,
            escalation_required=governance.escalation_required,
            governance_reason=governance.governance_reason,
        ),
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

def get_operational_control_summary(
    db: Session,
) -> OperationalControlSummary:
    """
    Build the consolidated operational control summary.

    The summary is derived from the existing operational risk
    queue and does not independently calculate financial impact
    or risk classification.
    """

    from app.services.operational_risk import (
        get_operational_risk_queue,
    )

    risk_queue = get_operational_risk_queue(db)

    total_known_financial_impact = sum(
        (
            item.financial_impact
            for item in risk_queue
            if item.financial_impact is not None
        ),
        Decimal("0"),
    )

    action_required_count = sum(
        1
        for item in risk_queue
        if item.attention_status == "ACTION_REQUIRED"
    )

    in_progress_count = sum(
        1
        for item in risk_queue
        if item.attention_status == "IN_PROGRESS"
    )

    human_resolution_required_count = sum(
        1
        for item in risk_queue
        if item.attention_status == "HUMAN_RESOLUTION_REQUIRED"
    )

    monitor_count = sum(
        1
        for item in risk_queue
        if item.attention_status == "MONITOR"
    )

    no_action_required_count = sum(
        1
        for item in risk_queue
        if item.attention_status == "NO_ACTION_REQUIRED"
    )

    outstanding_control_count = (
        action_required_count
        + in_progress_count
        + human_resolution_required_count
    )

    highest_priority_item = risk_queue[0] if risk_queue else None

    return OperationalControlSummary(
        total_exceptions=len(risk_queue),

        action_required_count=action_required_count,
        in_progress_count=in_progress_count,
        human_resolution_required_count=human_resolution_required_count,
        monitor_count=monitor_count,
        no_action_required_count=no_action_required_count,

        total_known_financial_impact=total_known_financial_impact,

        highest_priority_payment_id=(
            highest_priority_item.payment_id
            if highest_priority_item
            else None
        ),
        highest_priority_score=(
            highest_priority_item.priority_score
            if highest_priority_item
            else None
        ),
        highest_priority_financial_impact=(
            highest_priority_item.financial_impact
            if highest_priority_item
            else None
        ),

        outstanding_control_count=outstanding_control_count,
    )

def get_governed_operational_controls(db: Session) -> list[OperationalExceptionControl]:
    """
    Return only operational exceptions that currently require governance
    escalation.

    This is a read-only, deterministic view derived from the existing
    operational control state. It does not mutate financial records,
    exception lifecycle state, controlled actions, or audit logs.
    """
    controls = get_operational_exception_controls(db)

    governance_rank = {
        "CRITICAL": 4,
        "HIGH": 3,
        "ELEVATED": 2,
        "NORMAL": 1,
    }

    governed_controls = [
        control
        for control in controls
        if control.governance.escalation_required
    ]

    governed_controls.sort(
        key=lambda control: (
            governance_rank.get(control.governance.governance_level, 0),
            control.priority_score,
            (
                control.financial_impact
                if control.financial_impact is not None
                else Decimal("0")
            ),
        ),
        reverse=True,
    )

    return governed_controls