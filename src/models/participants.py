from typing import Optional, Union

from pydantic import BaseModel, validator


class Participant(BaseModel):
    id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    fax: Optional[str] = None
    website: Optional[str] = None
    communication_preference: Optional[str] = None
    communication_preference_rfr: Optional[str] = None
    communication_preference_disco: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[Union[int, str]] = None
    state: Optional[str] = None
    user_id: Optional[str] = None
    mycase_id: Optional[str] = None
    stripe_id: Optional[str] = None
    intercom_id: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    organization: Optional[str] = None

    # Mycase id as string or none
    @validator("mycase_id", pre=True)
    def mycase_id_as_string(cls, v):
        return str(v) or None
