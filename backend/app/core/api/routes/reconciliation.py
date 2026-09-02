from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.reconciliation import ReconciliationResult
from app.services.reconciliation import reconcile_payment


router = APIRouter(
    prefix="/reconciliation",
    tags=["reconciliation"],
)


@router.get(
    "/{payment_id}",
    response_model=ReconciliationResult,
)
def reconcile_payment_endpoint(
    payment_id: str,
    db: Session = Depends(get_db),
):
    result = reconcile_payment(
        db=db,
        payment_id=payment_id,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with payment_id '{payment_id}' not found.",
        )

    return result