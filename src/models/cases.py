from datetime import date, datetime
from typing import Dict, List, Optional, Union

import pandas as pd
from pydantic import BaseModel, validator


class Case(BaseModel):
    case_id: str
    court_id: str
    protection_order: Optional[bool]
    parties: Optional[List[Dict]]
    disposed: Optional[bool]
    legal_fileaccepted: Optional[bool]
    paper_accepted: Optional[bool]
    confidential: Optional[bool]
    display_judgenotes: Optional[bool]
    case_notecount: Optional[int]
    display_legalfileviewer: Optional[bool]
    display_fileviewer: Optional[bool]
    can_userseepublicdocuments: Optional[bool]
    can_userseecasedocuments: Optional[bool]
    can_userseeenoticehistory: Optional[bool]
    can_selectdocket: Optional[bool]
    can_seeecflinks: Optional[bool]
    can_seelegalfilelinks: Optional[bool]
    is_ticket: Optional[bool]
    address_a_type: Optional[str]
    address_city: Optional[str]
    address_line_1: Optional[str]
    address_seq_no: Optional[int]
    address_state_code: Optional[str]
    address_zip: Optional[str]
    birth_date: Optional[str]
    birth_date_code: Optional[str]
    criminal_case: Optional[bool]
    criminal_ind: Optional[str]
    description: Optional[str]
    description_code: Optional[str]
    first_name: Optional[str]
    year_of_birth: Optional[str]
    formatted_party_address: Optional[str]
    formatted_party_name: Optional[str]
    formatted_telephone: Optional[str]
    last_name: Optional[str]
    lit_ind: Optional[str]
    middle_name: Optional[str]
    party_type: Optional[str]
    pidm: Optional[int]
    pred_code: Optional[str]
    prosecuting_atty: Optional[bool]
    pty_seq_no: Optional[int]
    sort_seq: Optional[int]
    age: Optional[int]
    case_desc: Optional[str]
    court_desc: Optional[str]
    location: Optional[str]
    filing_date: Optional[datetime] = None
    case_date: Optional[datetime] = None
    formatted_filingdate: Optional[str]
    case_type: Optional[str]
    case_security: Optional[str]
    case_typecode: Optional[str]
    vine_code: Optional[str]
    locn_code: Optional[str]
    court_code: Optional[str]
    vine_display: Optional[str]
    vine_id: Optional[str]
    dockets: Optional[List[Dict]]
    documents: Optional[List[Dict]]
    charges: Optional[List[Dict]]
    judge: Optional[Dict]
    court_type: Optional[str]
    ticket_searchresult: Optional[Dict]
    fine: Optional[Dict]
    plea_andpayind: Optional[str]
    ticket: Optional[Dict]
    ticket_img: Optional[str]

    # Ignore parsing errors for now
    @validator("charges", pre=True, always=True)
    def set_charges(cls, v):
        return v or {}

    @validator("case_date", pre=True)
    def set_case_date(cls, v):
        try:
            v = pd.to_datetime(v)
            # convert to datetime
            return v.to_pydatetime()
        except Exception:
            return None

    @validator("filing_date", pre=True)
    def set_filing_date(cls, v):
        try:
            v = pd.to_datetime(v)
            # convert to datetime
            return v.to_pydatetime()
        except Exception:
            return None
