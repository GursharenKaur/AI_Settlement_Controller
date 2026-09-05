from app.db.database import SessionLocal
from app.models.exception import (
    ExceptionLifecycleStatus,
    ExceptionRecord,
)

from app.models.settlement import Settlement
from app.models.transaction import Transaction
from app.services.exception_intelligence import assess_exception
from app.services.reconciliation import reconcile_transaction
from app.services.exception_lifecycle import get_exception_record


def backfill_exception_lifecycles() -> None:
    db = SessionLocal()

    created = 0
    skipped_existing = 0
    skipped_matched = 0

    try:
        transactions = (
            db.query(Transaction)
            .order_by(Transaction.id)
            .all()
        )

        for transaction in transactions:
            payment_id = transaction.payment_id

            existing = get_exception_record(
                db=db,
                payment_id=payment_id,
            )

            if existing is not None:
                skipped_existing += 1
                continue

            settlement = (
                db.query(Settlement)
                .filter(
                    Settlement.payment_id == payment_id
                )
                .order_by(Settlement.id)
                .first()
            )

            reconciliation_result = reconcile_transaction(
                transaction=transaction,
                settlement=settlement,
            )

            assessment = assess_exception(
                reconciliation_result
            )

            if not assessment.is_exception:
                skipped_matched += 1
                continue

            record = ExceptionRecord(
                payment_id=payment_id,
                status=ExceptionLifecycleStatus.OPEN,
            )

            db.add(record)
            created += 1

        db.commit()

        print("========== LIFECYCLE BACKFILL ==========")
        print(f"Transactions checked : {len(transactions)}")
        print(f"Lifecycle records created : {created}")
        print(f"Existing records skipped : {skipped_existing}")
        print(f"Matched payments skipped : {skipped_matched}")
        print("Status : SUCCESS")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    backfill_exception_lifecycles()