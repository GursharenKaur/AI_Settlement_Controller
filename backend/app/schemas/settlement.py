from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SettlementCreate(BaseModel):
    settlement_id: str = Field(
        min_length=1,
        max_length=100,
    )

    payment_id: str = Field(
        min_length=1,
        max_length=100,
    )

    settled_amount: Decimal = Field(
        gt=0,
        decimal_places=2,
    )

    currency: str = Field(
        min_length=3,
        max_length=3,
    )

    status: str = Field(
        min_length=1,
        max_length=30,
    )

    settled_at: datetime


class SettlementResponse(BaseModel):
    id: int
    settlement_id: str
    payment_id: str
    settled_amount: Decimal
    currency: str
    status: str
    settled_at: datetime

    model_config = ConfigDict(from_attributes=True)