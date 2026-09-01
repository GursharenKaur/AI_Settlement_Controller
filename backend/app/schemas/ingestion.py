from pydantic import BaseModel, Field


class IngestionError(BaseModel):
    row: int = Field(ge=1)
    field: str = Field(min_length=1)
    message: str = Field(min_length=1)


class SettlementIngestionResult(BaseModel):
    received: int = Field(ge=0)
    created: int = Field(ge=0)
    duplicates: int = Field(ge=0)
    failed: int = Field(ge=0)
    errors: list[IngestionError] = Field(default_factory=list)