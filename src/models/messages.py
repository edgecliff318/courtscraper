from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator


class MessageTemplate(BaseModel):
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    template_type: Optional[str] = None
    template_text: Optional[str] = None
    template_language: Optional[str] = None
    media_enabled: Optional[bool] = False
    creation_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    @validator("last_updated", pre=True, always=True)
    def set_last_updated_date_now(cls, v):
        return v or datetime.now()

    @validator("creation_date", pre=True)
    def set_creation_date_now(cls, v):
        return v or datetime.now()


class Interaction(BaseModel):
    id: Optional[str] = None
    case_id: str
    creation_date: Optional[datetime] = None
    message: Optional[str] = None
    type: Optional[str] = None
    phone: Optional[str] = None
    direction: Optional[str] = None
    status: Optional[str] = None

    @validator("creation_date", pre=True)
    def set_creation_date_now(cls, v):
        return v or datetime.now()
