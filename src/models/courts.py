from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator


class Court(BaseModel):
    code: str
    type: Optional[str] = None
    availability: Optional[str] = None
    description: Optional[str] = None
    message: Optional[str] = None
    county_code: Optional[str] = None
    name: str
    creation_date: Optional[datetime] = None
    enabled: Optional[bool] = False
    state: Optional[str] = None

    @validator("creation_date", pre=True)
    def set_creation_date_now(cls, v):
        return v or datetime.now()
