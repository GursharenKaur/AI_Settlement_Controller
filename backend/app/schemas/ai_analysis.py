from pydantic import BaseModel


class AIExceptionAnalysis(BaseModel):
    payment_id: str
    explanation: str
    financial_impact_explanation: str
    risk_explanation: str
    recommended_action: str