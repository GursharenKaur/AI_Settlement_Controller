from collections import defaultdict
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.settlement import Settlement
from app.models.transaction import Transaction
from app.schemas.exception import ExceptionSeverity
from app.services.exception_intelligence import assess_exception
from app.services.reconciliation import reconcile_transaction


def get_exception_patterns(
    db: Session,
) -> dict:
    """
    Derive population-level exception patterns from authoritative
    transaction and settlement data.

    This service is read-only:
    - does not mutate financial records
    - does not create or modify ExceptionRecord
    - does not create controlled actions
    - does not resolve exceptions
    - does not create audit events
    - does not invoke AI
    - does not modify priority or governance

    Financial truth remains determined by the existing
    reconciliation and exception-assessment engines.
    """

    transactions = (
        db.query(Transaction)
        .order_by(Transaction.id)
        .all()
    )

    settlements = (
        db.query(Settlement)
        .order_by(Settlement.id)
        .all()
    )

    settlements_by_payment_id: dict[str, Settlement] = {}

    for settlement in settlements:
        settlement_payment_id = str(settlement.payment_id)

        # Preserve existing reconciliation behavior:
        # the first settlement ordered by ID is authoritative.
        if settlement_payment_id not in settlements_by_payment_id:
            settlements_by_payment_id[settlement_payment_id] = settlement

    pattern_data: dict = defaultdict(
        lambda: {
            "exception_count": 0,
            "high_severity_count": 0,
            "known_financial_impact_by_currency": defaultdict(
                lambda: Decimal("0")
            ),
        }
    )

    total_exceptions = 0

    for transaction in transactions:
        settlement = settlements_by_payment_id.get(
            str(transaction.payment_id)
        )

        reconciliation_result = reconcile_transaction(
            transaction=transaction,
            settlement=settlement,
        )

        assessment = assess_exception(reconciliation_result)

        if not assessment.is_exception:
            continue

        total_exceptions += 1

        category_data = pattern_data[assessment.category]

        category_data["exception_count"] += 1

        if assessment.severity == ExceptionSeverity.HIGH:
            category_data["high_severity_count"] += 1

        if (
            assessment.financial_impact is not None
            and transaction.currency is not None
        ):
            category_data[
                "known_financial_impact_by_currency"
            ][transaction.currency] += assessment.financial_impact

    categories = []

    for category in sorted(
        pattern_data,
        key=lambda value: value.value,
    ):
        category_data = pattern_data[category]

        categories.append(
            {
                "category": category,
                "exception_count": category_data["exception_count"],
                "high_severity_count": category_data[
                    "high_severity_count"
                ],
                "known_financial_impact_by_currency": dict(
                    category_data[
                        "known_financial_impact_by_currency"
                    ]
                ),
            }
        )

    recurring_categories = [
        category["category"]
        for category in categories
        if category["exception_count"] > 1
    ]

    return {
        "total_transactions": len(transactions),
        "total_exceptions": total_exceptions,
        "categories": categories,
        "recurring_categories": recurring_categories,
    }