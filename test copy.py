import logging

import pandas as pd

from src.core.config import get_settings
from src.services import leads
from src.services import messages
# get_interactions_filtered

logger = logging.Logger(__name__)

settings = get_settings()


def process_date(lead):
    # Creation date from ms timestamp
    try:
        creation_date = pd.to_datetime(lead.get("creation_date"), unit="ms")
    except Exception as e:
        logger.error(f"Error parsing creation_date: {e}")
        creation_date = pd.to_datetime(lead.get("creation_date"))

    # UTC to Central time
    creation_date = creation_date.tz_convert("America/Chicago")
    creation_date = creation_date.strftime("%Y-%m-%d %H:%M:%S")

    lead["creation_date"] = creation_date

    return lead


def render_inbound_leads(dates, status):
    (start_date, end_date) = dates

    leads_list = leads.get_leads(
        start_date=start_date,
        end_date=end_date,
        # source="website",
    )

    # Fields selection
    lead_fields = {
        "id",
        "case_id",
        "status",
    }
    message_fields = {
        "id",
        "case_id",
        "direction",
        "status",
        "creation_date",
    }

    # leads_list = [process_date(lead.model_dump(include=fields)) for lead in leads_list]

    # df = pd.DataFrame(leads_list)
    # print(df)
    # df.to_csv("leads.csv")
    print(leads_list)


if __name__ == "__main__":
     # Fields selection
    lead_fields = {
        "id",
        "case_id",
        "status",
    }
    message_fields = {
        "id",
        "case_id",
        "direction",
        "status",
        "creation_date",
    }
    messages_response = messages.get_interactions_filtered(
        start_date="2023-09-01",
        end_date="2024-01-16",
    )
    messages_list = []
    for message in messages_response:
        message_data =message.model_dump(include=message_fields)
        lead = leads.get_single_lead(message_data.get("case_id"))
        if lead:
            lead = lead.model_dump(include=lead_fields)
            message_data['status'] = lead.get('status')
        messages_list.append(message_data)
    print(messages_list)
    df = pd.DataFrame(messages_list)
    
    df.to_csv("leads2.csv")
   
