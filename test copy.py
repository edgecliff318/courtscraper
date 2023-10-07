from datetime import datetime , timedelta
from typing import Optional , List

import pandas as pd
from pydantic import BaseModel, validator

leads_statuses = [
    {"label": "All", "value": "all"},
    {"label": "New", "value": "new"},
    {
        "label": "Not Contacted",
        "value": "not_contacted",
    },
    {"label": "Not Found", "value": "not_found"},
    {"label": "Not Valid", "value": "not_valid"},
    {"label": "Not Prioritized", "value": "not_prioritized"},
    {"label": "Contacted", "value": "contacted"},
    {"label": "Mailed", "value": "mailed"},
    {"label": "Failed", "value": "failed"},
    {"label": "Lost", "value": "lost"},
    {"label": "Won", "value": "won"},
    {"label": "Wait", "value": "wait"},
    {"label": "Stop", "value": "stop"},
    {"label": "Yes", "value": "yes"},
    {"label": "Responded", "value": "responded"},
    {"label": "Processing", "value": "processing"},
    {"label": "Paid", "value": "paid"},
    {"label": "Converted", "value": "converted"},
    {"label": "Request for Representation", "value": "rpr"},
    {"label": "Closed", "value": "closed"},
]


class Lead(BaseModel):
    case_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    court_code: Optional[str] = None
    age: Optional[int] = None
    year_of_birth: Optional[int] = None
    email: Optional[str | dict] = None
    phone: Optional[str | dict | List[str]] = None
    address: Optional[str | dict] = None
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
    notes: Optional[str] = None
    # Json Report from BeenVerified
    report: Optional[dict] = None
    details: Optional[str] = None

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


import asyncio
from google.cloud import firestore
from twilio.rest import Client
# import datetime
from pprint import pprint


TWILIO_ACCOUNT_SID = "ACc675e16f153269ab1d8d4c5f3ae2ce8a"
TWILIO_AUTH_TOKEN  = "095c5fb2a0eea27b7c4e46c1fd12cf45"
TWILIO_MESSAGE_SERVICE_SID = "MG2b12454f63e7ee70aaac25dd4b333898"

from_date = (
            datetime.now() - timedelta(days=1)
        ).strftime("%Y-%m-%d")

to_date = (
            datetime.now() + timedelta(days=1)
        ).strftime("%Y-%m-%d")

# Initialize the Firestore AsyncClient
firestore_client = firestore.AsyncClient()
twilio_client  = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
db = firestore_client
async def list_all_collections():
    # Fetch root level collections
    collections = firestore_client.collections()

    # Print each collection name
    async for collection in collections:
        print(collection.id)

# asyncio.run(list_all_collections())

async def get_lead_by_phone(phone):
    """
    Fetch a lead from the database by phone number asynchronously.
    
    :param phone: The phone number of the lead to be retrieved.
    :return: Lead object if found, otherwise None.
    """
    selected_fields = [f for f in Lead.__fields__.keys() if f != "report2"]
    queried_leads_exact = db.collection("leads").select(selected_fields).where("phone", "==", phone).stream()
    queried_leads_in_list = db.collection("leads").select(selected_fields).where("phone", "array_contains", phone).stream()
    lead_objects = [Lead(**doc.to_dict()) async for doc in queried_leads_exact] + \
                   [Lead(**doc.to_dict()) async for doc in queried_leads_in_list]

    return lead_objects[0] if lead_objects else None

  
# messages_twilio = twilio_client.messages.list(
#         date_sent_after=from_date, date_sent_before=to_date
#     )


# for sms in messages_twilio:
#     pprint(vars(sms))

# pprint(get_lead_by_phone("+18166086456"))


import asyncio

# result = asyncio.run(get_lead_by_phone("+18166999499"))
# result = asyncio.run(get_lead_by_phone("0628594365"))
# print(result)
