from datetime import datetime

from pydantic import BaseModel

from app.models.exception import ExceptionLifecycleStatus


class ExceptionLifecycleResponse(BaseModel):
    payment_id: str
    status: ExceptionLifecycleStatus
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }