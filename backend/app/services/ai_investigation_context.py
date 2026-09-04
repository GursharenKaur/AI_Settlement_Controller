from app.schemas.ai_investigation import AIInvestigationContext
from app.services.historical_intelligence import (
    get_historical_exception_context,
)
from app.services.pattern_intelligence import get_exception_patterns


def build_ai_investigation_context(
    db,
    payment_id: str,
) -> AIInvestigationContext:
    """
    Build trusted deterministic context for AI-assisted investigation.

    All financial facts, exception classifications, recurrence signals,
    timing signals, and population patterns come from deterministic
    services.

    This function does not:
    - perform AI reasoning
    - modify financial state
    - modify priority or governance
    - create controlled actions
    - resolve exceptions
    - create audit events
    """

    historical_context = get_historical_exception_context(
        db=db,
        payment_id=payment_id,
    )

    pattern_context = get_exception_patterns(db=db)

    current_exception = historical_context["current_exception"]

    if current_exception is None:
        raise ValueError(
            f"Payment {payment_id} was not found"
        )

    historical = historical_context["historical_context"]

    return AIInvestigationContext(
        payment_id=payment_id,
        exception_category=current_exception["category"],
        severity=current_exception["severity"],
        financial_impact=current_exception["financial_impact"],
        priority_score=current_exception["priority_score"],
        historical_transaction_count=historical[
            "historical_transaction_count"
        ],
        historical_exception_count=historical[
            "historical_exception_count"
        ],
        same_category_exception_count=historical[
            "same_category_exception_count"
        ],
        same_currency_exception_count=historical[
            "same_currency_exception_count"
        ],
        same_category_and_currency_exception_count=historical[
            "same_category_and_currency_exception_count"
        ],
        recurrence_detected=historical["recurrence_detected"],
        timing_available=historical["timing_available"],
        settlement_delay_hours=historical[
            "settlement_delay_hours"
        ],
        historical_settlement_count=historical[
            "historical_settlement_count"
        ],
        historical_average_delay_hours=historical[
            "historical_average_delay_hours"
        ],
        timing_deviation_hours=historical[
            "timing_deviation_hours"
        ],
        population_total_transactions=pattern_context[
            "total_transactions"
        ],
        population_total_exceptions=pattern_context[
            "total_exceptions"
        ],
        recurring_categories=pattern_context[
            "recurring_categories"
        ],
    )