from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.exception import ExceptionRecord

from app.db.database import get_db
from app.services.exception_intelligence import assess_exception
from app.services.exception_overview import get_exception_overview
from app.services.reconciliation import reconcile_payment
from app.services.exception_summary import get_exception_summary
from app.services.ai_analysis import generate_exception_analysis
from app.services.ai_context import build_exception_ai_context
from app.services.ai_portfolio_analysis import generate_portfolio_analysis
from app.services.ai_portfolio_context import build_portfolio_ai_context
from app.schemas.ai_portfolio_analysis import AIPortfolioAnalysis
from app.models.exception import ExceptionLifecycleStatus
from app.schemas.exception_lifecycle import ExceptionLifecycleResponse
from app.services.exception_lifecycle import get_or_create_exception_record
from app.schemas.controller_decision import ControllerDecision
from app.services.controller_decision import build_controller_decision

router = APIRouter(
    prefix="/exceptions",
    tags=["Exceptions"],
)


@router.get("")
def get_exceptions(
    db: Session = Depends(get_db),
):
    return get_exception_overview(db)

@router.get("/summary")
def get_exception_summary_overview(
    db: Session = Depends(get_db),
):
    return get_exception_summary(db)

@router.get("/ai-analysis", response_model=AIPortfolioAnalysis)
def get_portfolio_ai_analysis(db: Session = Depends(get_db)):
    summary = get_exception_summary(db)
    context = build_portfolio_ai_context(summary)
    return generate_portfolio_analysis(context)

@router.post(
    "/{payment_id}/acknowledge",
    response_model=ExceptionLifecycleResponse,
)
def acknowledge_exception(
    payment_id: str,
    db: Session = Depends(get_db),
):
    record = get_or_create_exception_record(db, payment_id)

    if record.status == ExceptionLifecycleStatus.OPEN:
        record.status = ExceptionLifecycleStatus.ACKNOWLEDGED
        db.commit()
        db.refresh(record)

    return record


@router.post(
    "/{payment_id}/resolve",
    response_model=ExceptionLifecycleResponse,
)
def resolve_exception(
    payment_id: str,
    db: Session = Depends(get_db),
):
    record = get_or_create_exception_record(db, payment_id)

    if record.status == ExceptionLifecycleStatus.ACKNOWLEDGED:
        record.status = ExceptionLifecycleStatus.RESOLVED
        db.commit()
        db.refresh(record)

    return record

@router.get(
    "/{payment_id}/lifecycle",
    response_model=ExceptionLifecycleResponse,
)
def get_exception_lifecycle(
    payment_id: str,
    db: Session = Depends(get_db),
):
    return get_or_create_exception_record(db, payment_id)

@router.get(
    "/{payment_id}/decision",
    response_model=ControllerDecision,
)
def get_controller_decision(
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
            detail=f"Payment {payment_id} not found",
        )

    assessment = assess_exception(reconciliation_result)

    lifecycle_record = (
        db.query(ExceptionRecord)
        .filter(ExceptionRecord.payment_id == assessment.payment_id)
        .first()
    )

    assessment.lifecycle_status = (
        lifecycle_record.status
        if lifecycle_record is not None
        else None
    )

    return build_controller_decision(assessment)   

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

@router.get("/{payment_id}/ai-analysis")
def get_exception_ai_analysis(
    payment_id: str,
    db: Session = Depends(get_db),
):
    result = reconcile_payment(db, payment_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Payment {payment_id} not found",
        )

    assessment = assess_exception(result)

    summary = get_exception_summary(db)

    context = build_exception_ai_context(
        assessment=assessment,
        summary=summary,
    )

    return generate_exception_analysis(context)