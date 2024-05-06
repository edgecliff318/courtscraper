from tracemalloc import start
from typing import Optional

from pydantic import BaseModel, validator


class Account(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    url: Optional[str] = None
    api_key: Optional[str] = None
    active: bool = True
    system: Optional[str] = None
    start_date: Optional[int] = None
    end_date: Optional[int] = None
    details: Optional[dict] = None


class Settings(BaseModel):
    start_date: int
    end_date: int
    automated_message: Optional[str] = None
    automated_message_frequency: Optional[int] = None
    automated_message_period: Optional[list] = None
    automated_messaging: Optional[bool] = False
    automated_messaging_mapping: Optional[dict] = None

    # set start_date to 1 if not set
    @validator("start_date")
    def set_start_date(cls, v):
        return v or 2

    # set end_date to 1 if not set
    @validator("end_date")
    def set_end_date(cls, v):
        return v or 0


class UserSettings(BaseModel):
    email: Optional[str] = None
    signature: Optional[str] = None


class Scrapers(BaseModel):
    state: Optional[dict] = None
