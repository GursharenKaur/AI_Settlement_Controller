from sqlalchemy.orm import Session

from app.models.settlement import Settlement
from app.models.transaction import Transaction
from app.services.exception_intelligence import assess_exception
from app.services.reconciliation import reconcile_transaction
from app.schemas.exception import ExceptionAssessment


def get_exception_overview(db: Session) -> list[ExceptionAssessment]:
    transactions = db.query(Transaction).order_by(Transaction.id).all()

    assessments: list[ExceptionAssessment] = []

    for transaction in transactions:
        settlement = (
            db.query(Settlement)
            .filter(Settlement.payment_id == transaction.payment_id)
            .order_by(Settlement.id)
            .first()
        )

        reconciliation_result = reconcile_transaction(
            transaction=transaction,
            settlement=settlement,
        )

        assessment = assess_exception(reconciliation_result)
        assessments.append(assessment)

    assessments = [
        assessment
        for assessment in assessments
        if assessment.is_exception
    ]

    assessments.sort(
        key=lambda assessment: assessment.priority_score,
        reverse=True,
    )

    return assessments