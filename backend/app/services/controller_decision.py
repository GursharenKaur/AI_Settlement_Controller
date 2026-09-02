from app.schemas.controller_decision import (
    ControllerAction,
    ControllerDecision,
)
from app.schemas.exception import ExceptionAssessment


def build_controller_decision(
    assessment: ExceptionAssessment,
) -> ControllerDecision:
    """
    Build a deterministic operational recommendation from
    a trusted exception assessment.

    This function does not execute any financial action.
    It only recommends the next operational step.
    """

    if not assessment.is_exception:
        return ControllerDecision(
            payment_id=assessment.payment_id,
            exception_category=assessment.category,
            lifecycle_status=assessment.lifecycle_status,
            financial_impact=assessment.financial_impact,
            priority_score=assessment.priority_score,
            recommended_action=ControllerAction.NO_FURTHER_ACTION,
            decision_reason="No exception is present for this payment.",
            human_review_required=False,
        )

    if assessment.lifecycle_status == "RESOLVED":
        return ControllerDecision(
            payment_id=assessment.payment_id,
            exception_category=assessment.category,
            lifecycle_status=assessment.lifecycle_status,
            financial_impact=assessment.financial_impact,
            priority_score=assessment.priority_score,
            recommended_action=ControllerAction.NO_FURTHER_ACTION,
            decision_reason="The exception has already been resolved.",
            human_review_required=False,
        )

    if assessment.category.value == "MISSING_SETTLEMENT":
        return ControllerDecision(
            payment_id=assessment.payment_id,
            exception_category=assessment.category,
            lifecycle_status=assessment.lifecycle_status,
            financial_impact=assessment.financial_impact,
            priority_score=assessment.priority_score,
            recommended_action=(
                ControllerAction.INVESTIGATE_MISSING_SETTLEMENT
            ),
            decision_reason=(
                "The payment has no corresponding settlement and "
                "requires settlement investigation."
            ),
            human_review_required=True,
        )

    if assessment.category.value in {
        "UNDER_SETTLEMENT",
        "OVER_SETTLEMENT",
    }:
        return ControllerDecision(
            payment_id=assessment.payment_id,
            exception_category=assessment.category,
            lifecycle_status=assessment.lifecycle_status,
            financial_impact=assessment.financial_impact,
            priority_score=assessment.priority_score,
            recommended_action=ControllerAction.REVIEW_SETTLEMENT_AMOUNT,
            decision_reason=(
                "The settled amount differs from the expected payment "
                "amount and requires settlement amount review."
            ),
            human_review_required=True,
        )

    if assessment.category.value == "CURRENCY_MISMATCH":
        return ControllerDecision(
            payment_id=assessment.payment_id,
            exception_category=assessment.category,
            lifecycle_status=assessment.lifecycle_status,
            financial_impact=assessment.financial_impact,
            priority_score=assessment.priority_score,
            recommended_action=ControllerAction.REVIEW_CURRENCY_MISMATCH,
            decision_reason=(
                "The transaction and settlement currencies differ and "
                "require currency reconciliation review."
            ),
            human_review_required=True,
        )

    if assessment.category.value == "INVALID_STATE":
        return ControllerDecision(
            payment_id=assessment.payment_id,
            exception_category=assessment.category,
            lifecycle_status=assessment.lifecycle_status,
            financial_impact=assessment.financial_impact,
            priority_score=assessment.priority_score,
            recommended_action=ControllerAction.INVESTIGATE_INVALID_STATE,
            decision_reason=(
                "The transaction and settlement states form an invalid "
                "operational combination and require investigation."
            ),
            human_review_required=True,
        )

    raise ValueError(
        f"Unsupported exception category: {assessment.category}"
    )