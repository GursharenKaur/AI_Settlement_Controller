from pydantic import BaseModel


class AIPortfolioAnalysis(BaseModel):
    executive_summary: str
    key_risk_drivers: str
    financial_impact_explanation: str
    priority_assessment: str
    recommended_actions: str
    recommended_priority: str
    focus_category: str
    recommendation_reason: str
    human_review_required: bool