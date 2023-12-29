from datetime import datetime, timedelta

from rich.console import Console

from src.connectors.cloudtalk import (
    add_lead_cloud_talk,
    process_redudant_numbers,
)
from src.services import leads as leads_service

console = Console()


def upload_to_cloud_talk(limit=50, status="not_contacted", search_limit=2000):
    leads_list = leads_service.get_last_lead(
        status=status,
        limit=limit,
        search_limit=search_limit,
    )
    for lead in leads_list:
        if (
            lead.phones is not None
            and len(lead.phones) > 0
            and not lead.cloudtalk_upload
        ):
            if lead.last_updated < datetime.utcnow().astimezone() - timedelta(
                days=10
            ):
                console.log(f"Ignoring {lead.case_id} because it's too old.")
                continue
            try:
                add_lead_cloud_talk(lead)
            except Exception as e:
                console.log(
                    f"Error adding lead {lead.case_id} to CloudTalk: {e}"
                )
                continue

    console.log("Processing redundant numbers")
    process_redudant_numbers()
