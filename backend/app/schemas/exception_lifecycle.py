from datetime import datetime

from pydantic import BaseModel

from app.models.controlled_action import (
    ControlledActionStatus,
    ControlledActionType,
)
from app.models.exception import ExceptionLifecycleStatus


class ControlledActionLifecycleItem(BaseModel):
    id: int
    action_type: ControlledActionType
    status: ControlledActionStatus
    result: str | None
    executed_at: datetime | None

    model_config = {
        "from_attributes": True,
    }


class ExceptionLifecycleResponse(BaseModel):
    payment_id: str
    status: ExceptionLifecycleStatus
    created_at: datetime
    updated_at: datetime
    controlled_actions: list[ControlledActionLifecycleItem] = []

    model_config = {
        "from_attributes": True,
    }