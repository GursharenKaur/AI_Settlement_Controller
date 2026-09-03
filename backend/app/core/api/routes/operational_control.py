from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.operational_control import OperationalExceptionControl
from app.services.operational_control import (
    get_operational_exception_control,
    get_operational_exception_controls,
)

router = APIRouter(
    prefix="/control",
    tags=["Operational Control"],
)


@router.get(
    "/exceptions",
    response_model=list[OperationalExceptionControl],
)
def get_operational_control_exceptions(
    db: Session = Depends(get_db),
):
    """
    Return the current operational control view for all exceptions.

    This endpoint is read-only. It does not execute actions,
    change lifecycle state, modify financial records, or call AI.
    """

    return get_operational_exception_controls(db)


@router.get(
    "/exceptions/{payment_id}",
    response_model=OperationalExceptionControl,
)
def get_operational_control_exception(
    payment_id: str,
    db: Session = Depends(get_db),
):
    """
    Return the operational control view for one exception.
    """

    result = get_operational_exception_control(
        db=db,
        payment_id=payment_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No operational exception found for payment "
                f"{payment_id}"
            ),
        )

    return result
