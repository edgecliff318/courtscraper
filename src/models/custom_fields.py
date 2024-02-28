from datetime import datetime

from pydantic import BaseModel, validator


class CustomField(BaseModel):
    customer_id: str
    field_id: str
    entity_type: str
    label: str
    field_type: str
    options: list[str] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @validator("created_at", pre=True)
    def set_created_at_now(cls, v):
        return v or datetime.now()

    @validator("updated_at", pre=True)
    def set_updated_at_now(cls, v):
        return v or datetime.now()


class CustomerCustomFields(BaseModel):
    customer_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    details: dict | None = None
    fields: list[CustomField] | None = None

    @validator("created_at", pre=True)
    def set_created_at_now(cls, v):
        return v or datetime.now()

    @validator("updated_at", pre=True)
    def set_updated_at_now(cls, v):
        return v or datetime.now()
