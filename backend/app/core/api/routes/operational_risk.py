from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.operational_risk import (
    OperationalRiskItem,
    OperationalRiskSummary,
)

from app.services.operational_risk import (
    get_operational_risk_queue,
    get_operational_risk_summary,
)


router = APIRouter(
    prefix="/risk",
    tags=["Operational Risk"],
)


@router.get(
    "/queue",
    response_model=list[OperationalRiskItem],
)
def get_risk_queue(
    db: Session = Depends(get_db),
):
    """
    Return the deterministic operational risk queue.

    The endpoint is read-only. It does not:
    - modify financial records,
    - execute controlled actions,
    - change exception lifecycle state,
    - create audit events,
    - or call AI.
    """

    return get_operational_risk_queue(db)

@router.get(
    "/summary",
    response_model=OperationalRiskSummary,
)
def get_risk_summary(
    db: Session = Depends(get_db),
):
    """
    Return the deterministic operational risk summary.

    The endpoint is read-only. It does not:
    - modify financial records,
    - execute controlled actions,
    - change exception lifecycle state,
    - create audit events,
    - or call AI.
    """

    return get_operational_risk_summary(db)