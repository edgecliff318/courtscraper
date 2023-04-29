from typing import Dict, List, Optional, Union

from pydantic import BaseModel, validator


class Case(BaseModel):
    case_id: str
    state: Optional[str] = None
    disposition: Optional[str] = None
    judge: Optional[str] = None
    date_filed: Optional[str] = None
    location: Optional[str] = None
    case_type: Optional[str] = None
    court_type: Optional[str] = None
    court_city: Optional[str] = None
    court_jurisdiction: Optional[str] = None
    court_phone: Optional[str] = None
    court_time: Optional[str] = None
    client_birthdate: Optional[str] = None
    client_driver_license: Optional[str] = None
    offense: Optional[str] = None
    ticket_speed: Optional[str] = None
    ticket_posted_speed_limit: Optional[str] = None
    current_date: Optional[str] = None
    # Image is a binary file
    image: Optional[bytes] = None
    charges: Optional[str] = None
    dockets: Optional[List[Dict[str, Union[str, List]]]] = None
    dockets_entries: Optional[List[str]] = None
    services: Optional[
        Union[List[str], List[Dict[str, Union[str, List]]]]
    ] = None
    headers: Optional[Dict[str, str]] = None
    parties: Optional[str] = None

    # Ignore parsing errors for now
    @validator("charges", pre=True, always=True)
    def set_charges(cls, v):
        return v or {}
