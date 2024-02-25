from datetime import datetime

from pydantic import BaseModel, validator


class Project(BaseModel):
    project_id: str
    customer_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    title: str | None = None
    description: str | None = None
    details: dict | None = None
    status: str | None = None
    priority: str | None = None
    assigned_to: list[str] | None = None
    details: dict | None = None

    @validator("created_at", pre=True)
    def set_created_at_now(cls, v):
        return v or datetime.now()

    @validator("updated_at", pre=True)
    def set_updated_at_now(cls, v):
        return v or datetime.now()
