from app.schemas.controller_decision import (
    ControllerAction,
    ControllerDecision,
)
from app.schemas.exception import ExceptionCategory


ALLOWED_ACTIONS = {
    ExceptionCategory.MISSING_SETTLEMENT: (
        ControllerAction.INVESTIGATE_MISSING_SETTLEMENT
    ),
    ExceptionCategory.UNDER_SETTLEMENT: (
        ControllerAction.REVIEW_SETTLEMENT_AMOUNT
    ),
    ExceptionCategory.OVER_SETTLEMENT: (
        ControllerAction.REVIEW_SETTLEMENT_AMOUNT
    ),
    ExceptionCategory.CURRENCY_MISMATCH: (
        ControllerAction.REVIEW_CURRENCY_MISMATCH
    ),
    ExceptionCategory.INVALID_STATE: (
        ControllerAction.INVESTIGATE_INVALID_STATE
    ),
}


def validate_controller_action(
    decision: ControllerDecision,
    requested_action: ControllerAction,
) -> tuple[bool, str]:
    """
    Validate that a requested controlled action is permitted
    for the deterministic controller decision.

    This function does not execute any financial or operational action.
    It only validates the action boundary.
    """

    if decision.exception_category == ExceptionCategory.NONE:
        return False, "No controlled action is permitted for a non-exception."

    if decision.lifecycle_status == "RESOLVED":
        return False, "No controlled action is permitted for a resolved exception."

    expected_action = ALLOWED_ACTIONS.get(decision.exception_category)

    if expected_action is None:
        return False, "No controlled action is defined for this exception category."

    if requested_action != expected_action:
        return (
            False,
            f"Requested action '{requested_action.value}' is not permitted "
            f"for exception category "
            f"'{decision.exception_category.value}'.",
        )

    return True, "Controlled action is permitted."