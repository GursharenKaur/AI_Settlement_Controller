from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.settlement import SettlementCreate, SettlementResponse
from app.services.settlement_ingestion import ingest_settlement


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
    db_settlement, is_duplicate = ingest_settlement(
        db=db,
        settlement=settlement,
    )

    if is_duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Settlement with settlement_id "
                f"'{settlement.settlement_id}' already exists."
            ),
        )

    return db_settlement