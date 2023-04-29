from typing import Optional

from pydantic import BaseModel, validator


class Account(BaseModel):
    username: Optional[str]
    password: Optional[str]
    url: Optional[str]
    api_key: Optional[str]
    active: bool = True
    system: Optional[str]


class Settings(BaseModel):
    start_date: int
    end_date: int

    # set start_date to 1 if not set
    @validator("start_date")
    def set_start_date(cls, v):
        return v or 2

    # set end_date to 1 if not set
    @validator("end_date")
    def set_end_date(cls, v):
        return v or 0
