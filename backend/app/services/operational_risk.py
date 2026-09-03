from sqlalchemy.orm import Session

from app.schemas.operational_risk import OperationalRiskItem
from app.services.operational_control import (
    get_operational_exception_controls,
)


ATTENTION_RANK = {
    "ACTION_REQUIRED": 5,
    "IN_PROGRESS": 4,
    "HUMAN_RESOLUTION_REQUIRED": 3,
    "MONITOR": 2,
    "NO_ACTION_REQUIRED": 1,
}


def classify_attention_status(control) -> str:
    """
    Deterministically classify the operational attention state.

    Precedence:
    1. RESOLVED lifecycle -> NO_ACTION_REQUIRED
    2. IN_PROGRESS remediation -> IN_PROGRESS
    3. COMPLETED remediation while unresolved -> HUMAN_RESOLUTION_REQUIRED
    4. Human review required -> ACTION_REQUIRED
    5. Otherwise -> MONITOR

    This function does not:
    - modify financial records,
    - execute controlled actions,
    - change exception lifecycle state,
    - call AI,
    - or create audit events.
    """

    if control.lifecycle_status == "RESOLVED":
        return "NO_ACTION_REQUIRED"

    if control.remediation_status == "IN_PROGRESS":
        return "IN_PROGRESS"

    if (
        control.remediation_status == "COMPLETED"
        and control.lifecycle_status != "RESOLVED"
    ):
        return "HUMAN_RESOLUTION_REQUIRED"

    if control.human_review_required:
        return "ACTION_REQUIRED"

    return "MONITOR"


def get_operational_risk_queue(
    db: Session,
) -> list[OperationalRiskItem]:
    """
    Build the deterministic operational risk queue.

    Ordering:
    1. Operational attention status
    2. Priority score
    3. Known financial impact

    This function does not:
    - calculate a new financial impact,
    - call AI,
    - modify financial records,
    - execute controlled actions,
    - change exception lifecycle state,
    - or create audit events.
    """

    controls = get_operational_exception_controls(db)

    risk_items = [
        OperationalRiskItem(
            payment_id=control.payment_id,
            category=control.category,
            severity=control.severity,
            financial_impact=control.financial_impact,
            priority_score=control.priority_score,
            lifecycle_status=control.lifecycle_status,
            recommended_action=control.recommended_action,
            human_review_required=control.human_review_required,
            remediation_status=control.remediation_status,
            attention_status=classify_attention_status(control),
        )
        for control in controls
    ]

    risk_items.sort(
        key=lambda item: (
            ATTENTION_RANK[item.attention_status],
            item.priority_score,
            item.financial_impact or 0,
        ),
        reverse=True,
    )

    return risk_items