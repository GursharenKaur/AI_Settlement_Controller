from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.settlement import Settlement
from app.schemas.ingestion import SettlementIngestionResult
from app.schemas.settlement import SettlementCreate


def ingest_settlements(
    db: Session,
    settlements: list[SettlementCreate],
) -> SettlementIngestionResult:
    result = SettlementIngestionResult(
        received=len(settlements),
        created=0,
        duplicates=0,
        failed=0,
        errors=[],
    )

    for settlement in settlements:
        existing = (
            db.query(Settlement)
            .filter(
                Settlement.settlement_id == settlement.settlement_id
            )
            .first()
        )

        if existing is not None:
            result.duplicates += 1
            continue

        db_settlement = Settlement(
            settlement_id=settlement.settlement_id,
            payment_id=settlement.payment_id,
            settled_amount=settlement.settled_amount,
            currency=settlement.currency,
            status=settlement.status,
            settled_at=settlement.settled_at,
        )

        try:
            with db.begin_nested():
                db.add(db_settlement)
                db.flush()

        except IntegrityError:
            result.duplicates += 1
            continue

        result.created += 1

    db.commit()

    return result