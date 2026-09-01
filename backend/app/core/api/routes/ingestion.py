from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.ingestion import IngestionError, SettlementIngestionResult
from app.services.settlement_batch import ingest_settlements
from app.services.settlement_csv import parse_settlement_csv


router = APIRouter(
    prefix="/ingestion",
    tags=["ingestion"],
)


@router.post(
    "/settlements",
    response_model=SettlementIngestionResult,
    status_code=status.HTTP_200_OK,
)
def ingest_settlements_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported.",
        )

    settlements = []
    errors: list[IngestionError] = []
    received = 0

    for settlement, error in parse_settlement_csv(file.file):
        received += 1

        if error is not None:
            errors.append(error)
            continue

        if settlement is not None:
            settlements.append(settlement)

    result = ingest_settlements(
        db=db,
        settlements=settlements,
    )

    return SettlementIngestionResult(
        received=received,
        created=result.created,
        duplicates=result.duplicates,
        failed=len(errors),
        errors=errors,
    )