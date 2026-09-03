from sqlalchemy.orm import Session

from app.schemas.operational_risk import OperationalRiskItem
from app.services.operational_control import (
    get_operational_exception_controls,
)


def get_operational_risk_queue(
    db: Session,
) -> list[OperationalRiskItem]:
    """
    Build the deterministic operational risk queue.

    This function does not:
    - calculate a new financial impact,
    - call AI,
    - modify financial records,
    - execute controlled actions,
    - change exception lifecycle state,
    - or create audit events.

    It only converts the existing operational control view
    into a prioritized operational risk queue.
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
        )
        for control in controls
    ]

    risk_items.sort(
        key=lambda item: (
            item.priority_score,
            item.financial_impact or 0,
        ),
        reverse=True,
    )

    return risk_items