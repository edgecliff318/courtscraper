from datetime import datetime
from typing import Optional

import pandas as pd
from pydantic import BaseModel, validator


class Lead(BaseModel):
    case_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    court_code: Optional[str] = None
    age: Optional[int] = None
    year_of_birth: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    county: Optional[str] = None
    creation_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    case_date: Optional[datetime] = None
    status: Optional[str] = "new"
    source: Optional[str] = None
    charges_description: Optional[str] = None
    disposed: Optional[bool] = False
    carrier: Optional[str] = None

    @validator("last_updated", pre=True, always=True)
    def set_last_updated_date_now(cls, v):
        return v or datetime.now()

    @validator("creation_date", pre=True)
    def set_creation_date_now(cls, v):
        return v or datetime.now()

    @validator("age", pre=True)
    def set_age(cls, v):
        try:
            return int(v)
        except Exception:
            return None

    @validator("year_of_birth", pre=True)
    def set_year_of_birth(cls, v):
        try:
            return int(v)
        except Exception:
            return None

    @validator("case_date", pre=True)
    def set_case_date(cls, v):
        try:
            v = pd.to_datetime(v)
            # convert to datetime
            return v.to_pydatetime()
        except Exception:
            return None
