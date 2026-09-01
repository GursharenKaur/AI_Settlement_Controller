from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.settlement import Settlement
from app.schemas.settlement import SettlementCreate, SettlementResponse


router = APIRouter(
    prefix="/settlements",
    tags=["settlements"],
)


@router.post(
    "",
    response_model=SettlementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_settlement(
    settlement: SettlementCreate,
    db: Session = Depends(get_db),
):
    db_settlement = Settlement(
        settlement_id=settlement.settlement_id,
        payment_id=settlement.payment_id,
        settled_amount=settlement.settled_amount,
        currency=settlement.currency,
        status=settlement.status,
        settled_at=settlement.settled_at,
    )

    db.add(db_settlement)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Settlement with settlement_id "
                f"'{settlement.settlement_id}' already exists."
            ),
        )

    db.refresh(db_settlement)

    return db_settlement