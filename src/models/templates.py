from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator


class Template(BaseModel):
    id: Optional[str] = None
    name: str
    creation_date: Optional[datetime] = None
    update_date: Optional[datetime] = None
    enabled: Optional[bool] = True
    category: Optional[str] = None
    creator: Optional[str] = None
    type: Optional[str] = "file"  # file, html, text
    text: Optional[str] = None
    filepath: Optional[str] = None

    @validator("creation_date", pre=True)
    def set_creation_date_now(cls, v):
        return v or datetime.now()

    @validator("update_date", pre=True)
    def set_update_date_now(cls, v):
        return v or datetime.now()

    @validator("creator", pre=True)
    def set_creator(cls, v):
        return v or "admin"
