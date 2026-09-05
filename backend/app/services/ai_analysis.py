from app.schemas.ai_analysis import AIExceptionAnalysis
from app.schemas.ai_context import ExceptionAIContext
from app.services.gemini_client import client


MODEL_NAME = "gemini-3.6-flash"


def generate_exception_analysis(
    context: ExceptionAIContext,
) -> AIExceptionAnalysis:
    """
    Generate a structured AI analysis of a settlement exception.

    Deterministic financial facts are supplied through the trusted
    context. Gemini is responsible only for explanation and
    recommendation.
    """

    prompt = f"""
You are an AI financial operations analyst for a payment
settlement reconciliation system inspired by Razorpay.

Analyze the following trusted exception data.

Payment ID: {context.payment_id}
Exception Category: {context.exception_category.value}
Severity: {context.severity.value}
Known Financial Impact: {context.financial_impact}
Priority Score: {context.priority_score}
Overall Portfolio Risk Band: {context.overall_risk_band}
Overall Portfolio Financial Risk Level: {context.overall_financial_risk_level}

Important rules:
1. Do not invent financial amounts.
2. Do not change or reinterpret the supplied financial impact.
3. If financial impact is None, explicitly state that it cannot
   be safely quantified from the available data.
4. Explain the operational significance of the exception.
5. Recommend a practical investigation or operational action.
6. Return only the requested structured analysis.
7. The overall portfolio risk band and overall portfolio financial risk
   level describe the broader exception portfolio. Do not present them
   as if they were independently calculated financial risk values for
   this individual payment.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": AIExceptionAnalysis,
        },
    )

    return AIExceptionAnalysis.model_validate_json(response.text)