from app.schemas.ai_investigation import (
    AIInvestigationAnalysis,
    AIInvestigationContext,
)
from app.services.gemini_client import client


MODEL_NAME = "gemini-3.6-flash"

class AIInvestigationError(Exception):
    """Raised when AI investigation generation fails."""


def generate_investigation_analysis(
    context: AIInvestigationContext,
) -> AIInvestigationAnalysis:
    """
    Generate an AI-assisted investigation explanation from
    trusted deterministic settlement intelligence.

    Gemini may explain the supplied evidence and provide
    investigation guidance, but it must not make financial,
    priority, governance, remediation, or resolution decisions.
    """

    prompt = f"""
You are an AI financial operations investigation assistant for
a payment settlement reconciliation system inspired by Razorpay.

You are given TRUSTED, DETERMINISTIC evidence produced by the
settlement reconciliation and intelligence system.

Analyze the evidence for the operator.

PAYMENT
Payment ID: {context.payment_id}
Exception Category: {context.exception_category.value}
Severity: {context.severity.value}
Known Financial Impact: {context.financial_impact}
Deterministic Priority Score: {context.priority_score}

HISTORICAL CONTEXT
The historical transaction and exception counts below refer to
the broader transaction population AFTER excluding the current
payment being investigated.
They do NOT mean that the current payment itself has this number
of historical transactions or historical exception records.
Historical Transaction Count (excluding current payment):
{context.historical_transaction_count}
Historical Exception Count (excluding current payment):
{context.historical_exception_count}
Same Category Exception Count: {context.same_category_exception_count}
Same Currency Exception Count: {context.same_currency_exception_count}
Same Category + Currency Exception Count:
{context.same_category_and_currency_exception_count}
Recurrence Detected: {context.recurrence_detected}

TIMING CONTEXT
Timing Available: {context.timing_available}
Current Settlement Delay Hours: {context.settlement_delay_hours}
Historical Settlement Count: {context.historical_settlement_count}
Historical Average Delay Hours:
{context.historical_average_delay_hours}
Timing Deviation Hours: {context.timing_deviation_hours}

POPULATION CONTEXT
Population Transaction Count:
{context.population_total_transactions}
Population Exception Count:
{context.population_total_exceptions}
Recurring Exception Categories:
{context.recurring_categories}

IMPORTANT CONTROL RULES

1. Treat all supplied financial amounts as authoritative.
2. Do not invent financial amounts or financial facts.
3. Do not calculate a new financial risk score.
4. Do not change or reinterpret the supplied priority score.
5. Do not change severity or exception category.
6. Do not recommend a new priority.
7. Do not recommend a governance level.
8. Do not create, execute, or recommend a controlled remediation action.
9. Do not resolve or acknowledge the exception.
10. Do not claim that the payment is fraudulent or suspicious
    unless such evidence is explicitly supplied. No fraud evidence
    has been supplied here.
11. Distinguish clearly between observed evidence and possible
    investigation questions.
12. If timing is unavailable, explicitly state that timing cannot
    currently be assessed.
13. Do not treat a large timing deviation as proof of an anomaly;
    describe it only as contextual evidence.
14. Do not treat recurrence_detected as proof of cause.
15. Do not invent a reason for an exception.
16. Treat the supplied deterministic exception category,
    severity, financial impact, and priority as authoritative
    system outputs. Do not ask the operator to recalculate,
    override, or challenge those values.
17. Investigation guidance may ask the human operator to
    investigate the operational cause of observed behavior,
    including timing deviations, missing settlements, or
    reconciliation outcomes, but must not frame the deterministic
    financial result itself as untrusted.
18. Clearly identify important evidence gaps.
19. Provide practical investigation guidance for a human operator.
20. Human review remains mandatory.
21. Return only the requested structured analysis.
The response must contain:
- investigation_summary
- historical_context_explanation
- timing_context_explanation
- evidence_gaps
- investigation_guidance
Do not describe population-level historical transactions or
exceptions as if they belong to the current payment.
RECURRENCE SEMANTICS

The recurrence_detected field is a deterministic population-level
signal based on the supplied same-category exception count.

It does NOT mean that the current payment has previously experienced
the same exception.

Do not describe recurrence_detected as recurrence "for this payment"
or as historical incidents belonging to the current payment.

The same_category_exception_count, same_currency_exception_count,
and same_category_and_currency_exception_count are also population-level
counts among historical transactions excluding the current payment.
When discussing recurrence, describe it only as a population-level
pattern among historical transactions excluding the current payment.
Do not infer per-payment recurrence.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": AIInvestigationAnalysis,
            },
        )

        return AIInvestigationAnalysis.model_validate_json(response.text)

    except Exception as exc:
        raise AIInvestigationError(
            "AI investigation generation failed"
        ) from exc