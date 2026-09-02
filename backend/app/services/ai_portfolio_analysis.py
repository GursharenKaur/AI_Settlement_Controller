from app.schemas.ai_portfolio_analysis import AIPortfolioAnalysis
from app.schemas.ai_portfolio_context import PortfolioAIContext
from app.services.gemini_client import client


MODEL_NAME = "gemini-2.5-flash"


def generate_portfolio_analysis(
    context: PortfolioAIContext,
) -> AIPortfolioAnalysis:
    """
    Generate a portfolio-level AI analysis.

    All financial metrics and risk signals are supplied by the
    deterministic portfolio context. Gemini is responsible only
    for interpretation and operational recommendations.
    """

    prompt = f"""
You are an AI financial operations analyst for a payment
settlement reconciliation system inspired by Razorpay.

Analyze the following trusted portfolio-level exception data.

Total Transactions: {context.total_transactions}
Total Exceptions: {context.total_exceptions}
Exception Rate: {context.exception_rate}%
Total Known Financial Impact: {context.total_known_financial_impact}
Financial Impact Rate: {context.financial_impact_rate}%

Financial Impact By Category:
{context.financial_impact_by_category}

Exception Counts By Category:
{context.category_counts}

Exception Counts By Severity:
{context.severity_counts}

High Priority Exception Count: {context.high_priority_count}
Highest Priority Score: {context.highest_priority_score}
Dominant Exception Category: {context.dominant_exception_category}

Overall Risk Band: {context.overall_risk_band}
Overall Financial Risk Level: {context.overall_financial_risk_level}

Important rules:
1. Do not invent financial amounts.
2. Do not change or reinterpret any supplied financial metric.
3. Use the supplied financial impact by category when explaining
   monetary exposure.
4. Do not calculate monetary impact for categories where no
   financial impact is supplied.
5. Distinguish known financial impact from potential or
   unquantified risk.
6. Identify the most important operational risk drivers.
7. Explain which exception categories should be addressed first
   and why.
8. Recommend practical actions for a finance or operations team.
9. Return only the requested structured analysis.
10. Select one primary exception category as the focus category
    for immediate operational attention.
11. Assign a recommended priority using only the supplied risk,
    severity, exception counts, and known financial impact.
12. The recommended priority must reflect operational urgency,
    not an invented monetary estimate.
12A. The recommended priority must be exactly one of:
     CRITICAL, HIGH, MEDIUM, LOW.
     Do not use alternatives such as URGENT, SEVERE, IMMEDIATE,
     or other priority labels.
13. Set human_review_required to true. Financial or settlement
    actions must not be performed autonomously.
14. The focus category must be one of the exception categories
    present in the supplied data.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": AIPortfolioAnalysis,
        },
    )

    return AIPortfolioAnalysis.model_validate_json(response.text)