from typing import Optional, Union
from pydantic import BaseModel


class Participant(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    communication_preference: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[Union[int, str]] = None
    state: Optional[str] = None
    user_id: Optional[str] = None
    stripe_id: Optional[str] = None
    intercom_id: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    organization: Optional[str] = None
