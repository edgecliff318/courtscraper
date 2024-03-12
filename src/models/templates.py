from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator


class Template(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    creation_date: Optional[datetime] = None
    update_date: Optional[datetime] = None
    enabled: Optional[bool] = True
    category: Optional[str] = None
    creator: Optional[str] = None
    type: Optional[str] = "file"  # file, html, text, form
    subject: Optional[str] = None
    text: Optional[str] = None
    filepath: Optional[str] = None
    parameters: Optional[dict] = None
    state: Optional[str] = None
    user: Optional[str] = None
    trigger: Optional[str] = None
    repeat: Optional[bool] = False
    sms: Optional[bool] = False
    sms_message: Optional[str] = None
    next_case_status: Optional[str] = None

    @validator("creation_date", pre=True)
    def set_creation_date_now(cls, v):
        return v or datetime.now()

    @validator("update_date", pre=True)
    def set_update_date_now(cls, v):
        return v or datetime.now()

    @validator("creator", pre=True)
    def set_creator(cls, v):
        return v or "admin"


class TemplateV2(BaseModel):
    customer_id: str
    template_id: str
    type: str | None = None
    details: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @validator("created_at", pre=True)
    def set_created_at_now(cls, v):
        return v or datetime.now()

    @validator("updated_at", pre=True)
    def set_updated_at_now(cls, v):
        return v or datetime.now()
