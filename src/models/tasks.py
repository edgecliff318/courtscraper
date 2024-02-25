from datetime import datetime

from pydantic import BaseModel, validator


class Task(BaseModel):
    customer_id: str
    task_id: str
    project_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    title: str | None = None
    description: str | None = None
    template_id: str | None = None
    details: str | None = None
    type: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: datetime | None = None
    assigned_to: str | None = None

    @validator("created_at", pre=True)
    def set_created_at_now(cls, v):
        return v or datetime.now()

    @validator("updated_at", pre=True)
    def set_updated_at_now(cls, v):
        return v or datetime.now()
