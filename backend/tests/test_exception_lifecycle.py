from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.exception import ExceptionLifecycleStatus, ExceptionRecord
from app.models.settlement import Settlement
from app.models.transaction import Transaction
from app.services.exception_lifecycle import ensure_exception_lifecycle


def create_test_session():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    Session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    return Session()


def test_exception_creates_open_lifecycle():
    db = create_test_session()

    transaction = Transaction(
        payment_id="TEST-MISSING-001",
        amount=Decimal("1000.00"),
        currency="INR",
        status="paid",
        paid_at=datetime.now(timezone.utc),
    )

    db.add(transaction)
    db.flush()

    record = ensure_exception_lifecycle(
        db=db,
        payment_id="TEST-MISSING-001",
    )

    assert record is not None
    assert record.payment_id == "TEST-MISSING-001"
    assert record.status == ExceptionLifecycleStatus.OPEN

    db.rollback()
    db.close()


def test_matched_transaction_does_not_create_lifecycle():
    db = create_test_session()

    transaction = Transaction(
        payment_id="TEST-MATCHED-001",
        amount=Decimal("1000.00"),
        currency="INR",
        status="paid",
        paid_at=datetime.now(timezone.utc),
    )

    settlement = Settlement(
        settlement_id="TEST-SETTLEMENT-001",
        payment_id="TEST-MATCHED-001",
        settled_amount=Decimal("1000.00"),
        currency="INR",
        status="settled",
        settled_at=datetime.now(timezone.utc),
    )

    db.add(transaction)
    db.add(settlement)
    db.flush()

    record = ensure_exception_lifecycle(
        db=db,
        payment_id="TEST-MATCHED-001",
    )

    assert record is None

    stored_record = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.payment_id == "TEST-MATCHED-001"
        )
        .first()
    )

    assert stored_record is None

    db.rollback()
    db.close()


def test_existing_lifecycle_is_preserved():
    db = create_test_session()

    transaction = Transaction(
        payment_id="TEST-EXISTING-001",
        amount=Decimal("1000.00"),
        currency="INR",
        status="paid",
        paid_at=datetime.now(timezone.utc),
    )

    db.add(transaction)
    db.flush()

    existing = ExceptionRecord(
        payment_id="TEST-EXISTING-001",
        status=ExceptionLifecycleStatus.ACKNOWLEDGED,
    )

    db.add(existing)
    db.flush()

    record = ensure_exception_lifecycle(
        db=db,
        payment_id="TEST-EXISTING-001",
    )

    assert record is existing
    assert record.status == ExceptionLifecycleStatus.ACKNOWLEDGED

    db.rollback()
    db.close()