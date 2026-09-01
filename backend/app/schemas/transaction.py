from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    payment_id: str = Field(
        min_length=1,
        max_length=100
    )

    amount: Decimal = Field(
        gt=0,
        decimal_places=2
    )

    currency: str = Field(
        min_length=3,
        max_length=3
    )

    status: str = Field(
        min_length=1,
        max_length=30
    )


class TransactionResponse(BaseModel):
    id: int
    payment_id: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)