from datetime import datetime

from pydantic import BaseModel, Field

from app.models.controlled_action import (
    ControlledActionStatus,
    ControlledActionType,
)


class ControlledActionCreate(BaseModel):
    payment_id: str = Field(
        min_length=1,
        max_length=100,
    )
    action_type: ControlledActionType

class ControlledActionResponse(BaseModel):
    id: int
    payment_id: str
    action_type: ControlledActionType
    status: ControlledActionStatus
    reason: str
    result: str | None
    executed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }