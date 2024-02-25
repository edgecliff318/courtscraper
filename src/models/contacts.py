from datetime import datetime

from pydantic import BaseModel, validator


class Contact(BaseModel):
    customer_id: str
    contact_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    notes: str | None = None

    @validator("created_at", pre=True)
    def set_created_at_now(cls, v):
        return v or datetime.now()

    @validator("updated_at", pre=True)
    def set_updated_at_now(cls, v):
        return v or datetime.now()
