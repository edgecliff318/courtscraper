import typing as t
from enum import Enum

from pydantic import BaseModel, Field
import datetime as dt
import pytz



class Status(Enum, str):
    queued = "queued"
    sending = "sending"
    sent = "sent"
    failed = "failed"
    delivered = "delivered"
    undelivered = "undelivered"
    receiving = "receiving"
    received = "received"
    
    @classmethod
    def choices(cls):
        return [(choice.value, choice.value) for choice in cls]
    
  
# status_callback Twilio
def status_callback():
    pass

class MessageInfo(BaseModel):
    first_name: str = Field(..., description="First name of the person")
    last_name: str = Field(..., description="Last name of the person")
    phone: str = Field(..., description="Phone number of the person")
    email: str = Field(..., description="Email of the person")
    smg_status: Status = Field(..., description="Status of the SMS")
    case_id: str = Field(..., description="Case ID of the person")
    sid: str = Field(..., description="SID of the SMS")
    created_at: t.Optional[dt.datetime] = Field(
        default_factory=lambda: dt.datetime.now(pytz.timezone("US/Eastern")),
    )
    updated_at: t.Optional[dt.datetime] = Field(
        default_factory=lambda: dt.datetime.now(pytz.timezone("US/Eastern")),
    )
    retry_count: int = Field(default=0, description="Number of times the SMS has been retried")
    
    
        
