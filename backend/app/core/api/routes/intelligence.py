from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.historical_intelligence import (
    HistoricalExceptionIntelligenceResponse,
)
from app.services.historical_intelligence import (
    get_historical_exception_context,
)

from app.schemas.pattern_intelligence import PatternIntelligenceResponse
from app.services.pattern_intelligence import get_exception_patterns

router = APIRouter(
    prefix="/intelligence",
    tags=["intelligence"],
)


@router.get(
    "/exceptions/{payment_id}",
    response_model=HistoricalExceptionIntelligenceResponse,
)
def get_exception_intelligence(
    payment_id: str,
    db: Session = Depends(get_db),
):
    return get_historical_exception_context(
        db=db,
        payment_id=payment_id,
    )

@router.get(
    "/patterns",
    response_model=PatternIntelligenceResponse,
)
def get_patterns(
    db: Session = Depends(get_db),
):
    return get_exception_patterns(db=db)