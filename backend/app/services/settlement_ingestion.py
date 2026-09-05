from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.settlement import Settlement
from app.services.exception_lifecycle import ensure_exception_lifecycle
from app.schemas.settlement import SettlementCreate


def ingest_settlement(
    db: Session,
    settlement: SettlementCreate,
) -> tuple[Settlement | None, bool]:
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
        db.flush()

        ensure_exception_lifecycle(
            db=db,
            payment_id=settlement.payment_id,
        )

        db.commit()
    except IntegrityError:
        db.rollback()
        return None, True

    db.refresh(db_settlement)

    return db_settlement, False