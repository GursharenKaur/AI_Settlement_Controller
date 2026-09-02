from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict


class ReconciliationStatus(str, Enum):
    MATCHED = "MATCHED"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    MISSING_SETTLEMENT = "MISSING_SETTLEMENT"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    INVALID_STATE = "INVALID_STATE"


class DriftDirection(str, Enum):
    NONE = "NONE"
    UNDER_SETTLED = "UNDER_SETTLED"
    OVER_SETTLED = "OVER_SETTLED"


class ReconciliationResult(BaseModel):
    payment_id: str

    status: ReconciliationStatus

    expected_amount: Decimal
    actual_settled_amount: Decimal | None

    drift: Decimal | None
    drift_direction: DriftDirection

    transaction_currency: str
    settlement_currency: str | None

    model_config = ConfigDict(from_attributes=True)