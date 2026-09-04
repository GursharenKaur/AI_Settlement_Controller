from enum import Enum

from pydantic import BaseModel, Field


class ResolutionReason(str, Enum):
    SETTLEMENT_CONFIRMED = "SETTLEMENT_CONFIRMED"
    MANUAL_RECONCILIATION = "MANUAL_RECONCILIATION"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    DUPLICATE_EXCEPTION = "DUPLICATE_EXCEPTION"
    OTHER = "OTHER"


class ExceptionResolutionRequest(BaseModel):
    resolution_reason: ResolutionReason
    resolution_note: str = Field(
        min_length=1,
        max_length=1000,
    )