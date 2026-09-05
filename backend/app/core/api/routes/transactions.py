from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.services.exception_lifecycle import ensure_exception_lifecycle
from app.db.database import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionResponse


router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
)


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
):
    db_transaction = Transaction(
        payment_id=transaction.payment_id,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status,
        paid_at=transaction.paid_at,
    )

    db.add(db_transaction)

    try:
        db.flush()

        ensure_exception_lifecycle(
            db=db,
            payment_id=transaction.payment_id,
        )

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transaction with payment_id '{transaction.payment_id}' already exists.",
        )

    db.refresh(db_transaction)

    return db_transaction


@router.get(
    "",
    response_model=list[TransactionResponse],
)
def list_transactions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    transactions = (
        db.query(Transaction)
        .order_by(Transaction.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return transactions


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id '{transaction_id}' not found.",
        )

    return transaction