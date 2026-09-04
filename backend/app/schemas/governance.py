from pydantic import BaseModel


class GovernanceClassificationResponse(BaseModel):
    governance_level: str
    escalation_required: bool
    governance_reason: str