from fastapi import APIRouter, Depends, HTTPException
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

from app.schemas.ai_investigation import AIInvestigationAnalysis
from app.services.ai_investigation import (
    AIInvestigationError,
    generate_investigation_analysis,
)
from app.services.ai_investigation_context import build_ai_investigation_context

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

@router.get(
    "/exceptions/{payment_id}/investigation",
    response_model=AIInvestigationAnalysis,
)
def get_exception_investigation(
    payment_id: str,
    db: Session = Depends(get_db),
):
    try:
        context = build_ai_investigation_context(
            db=db,
            payment_id=payment_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    try:
        return generate_investigation_analysis(context)
    except AIInvestigationError as exc:
        raise HTTPException(
            status_code=503,
            detail="AI investigation service is temporarily unavailable",
        ) from exc