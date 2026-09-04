from sqlalchemy.orm import Session

from app.schemas.operational_risk import (
    OperationalRiskItem,
    OperationalRiskSummary,
)

from app.services.operational_control import (
    get_operational_exception_controls,
)
from decimal import Decimal

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
            age_minutes=control.age_minutes,
            age_hours=control.age_hours,
            aging_band=control.aging_band,
            lifecycle_status=control.lifecycle_status,
            recommended_action=control.recommended_action,
            human_review_required=control.human_review_required,
            remediation_status=control.remediation_status,
            attention_status=classify_attention_status(control),
            governance=control.governance,
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

def get_operational_risk_summary(
    db: Session,
) -> OperationalRiskSummary:
    """
    Build a deterministic operational risk summary
    from the operational risk queue.

    This function does not:
    - recalculate financial impact,
    - call AI,
    - modify financial records,
    - execute controlled actions,
    - change lifecycle state,
    - or create audit events.
    """

    risk_items = get_operational_risk_queue(db)

    attention_counts = {
        "ACTION_REQUIRED": 0,
        "IN_PROGRESS": 0,
        "HUMAN_RESOLUTION_REQUIRED": 0,
        "MONITOR": 0,
        "NO_ACTION_REQUIRED": 0,
    }

    total_known_financial_impact = Decimal("0")

    for item in risk_items:
        attention_counts[item.attention_status] += 1

        if item.financial_impact is not None:
            total_known_financial_impact += item.financial_impact

    actionable_items = [
        item
        for item in risk_items
        if item.attention_status != "NO_ACTION_REQUIRED"
    ]

    if actionable_items:
        highest_priority = actionable_items[0]

        highest_priority_payment_id = (
            highest_priority.payment_id
        )
        highest_priority_score = (
            highest_priority.priority_score
        )
        highest_priority_financial_impact = (
            highest_priority.financial_impact
        )
    else:
        highest_priority_payment_id = None
        highest_priority_score = None
        highest_priority_financial_impact = None

    return OperationalRiskSummary(
        total_exceptions=len(risk_items),
        action_required_count=attention_counts["ACTION_REQUIRED"],
        in_progress_count=attention_counts["IN_PROGRESS"],
        human_resolution_required_count=(
            attention_counts["HUMAN_RESOLUTION_REQUIRED"]
        ),
        monitor_count=attention_counts["MONITOR"],
        no_action_required_count=(
            attention_counts["NO_ACTION_REQUIRED"]
        ),
        total_known_financial_impact=(
            total_known_financial_impact
        ),
        highest_priority_payment_id=(
            highest_priority_payment_id
        ),
        highest_priority_score=(
            highest_priority_score
        ),
        highest_priority_financial_impact=(
            highest_priority_financial_impact
        ),
    )