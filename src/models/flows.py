from datetime import datetime

from pydantic import BaseModel, validator


class Flow(BaseModel):
    flow_id: str
    customer_id: str
    type: str | None = None
    description: str | None = None
    steps: list[dict[str, str]] | None = None
    details: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @validator("created_at", pre=True)
    def set_created_at_now(cls, v):
        return v or datetime.now()

    @validator("updated_at", pre=True)
    def set_updated_at_now(cls, v):
        return v or datetime.now()
