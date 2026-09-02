from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.exception_intelligence import assess_exception
from app.services.exception_overview import get_exception_overview
from app.services.reconciliation import reconcile_payment


router = APIRouter(
    prefix="/exceptions",
    tags=["Exceptions"],
)


@router.get("")
def get_exceptions(
    db: Session = Depends(get_db),
):
    return get_exception_overview(db)


@router.get("/{payment_id}")
def get_exception(
    payment_id: str,
    db: Session = Depends(get_db),
):
    reconciliation_result = reconcile_payment(
        db=db,
        payment_id=payment_id,
    )

    if reconciliation_result is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return assess_exception(reconciliation_result)