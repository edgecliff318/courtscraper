import logging

import typer
from rich.console import Console

from src.models import leads as leads_model
from src.scrapers.beenverified import BeenVerifiedScrapper
from src.services import leads as leads_service

console = Console()

logger = logging.getLogger()


def retrieve_leads():
    while True:
        leads = leads_service.get_leads(status="new")
        scrapper = BeenVerifiedScrapper(cache=False)
        console.print("Logged to BeenVerified")
        error_count = 0
        for lead in leads:
            try:
                lead_data = lead.dict()
                link = scrapper.get_beenverified_link(
                    first_name=lead.first_name,
                    last_name=lead.last_name,
                    year=lead.year_of_birth,
                )
                data = scrapper.retrieve_information(link)
                lead_data["phone"] = data.get("phone")
                lead_data["details"] = data.get("details")
                lead_data["email"] = data.get("email")
                lead_data["status"] = "not_contacted"
                leads_service.insert_lead(leads_model.Lead(**lead_data))
                console.log(f"Lead {lead.case_id} retrieved")
                error_count = 0
            except Exception as e:
                logger.error(f"Error retrieving lead {lead.case_id} - {e}")
                console.log(f"Error retrieving lead {lead.case_id} - {e}")
                error_count += 1
                # Sleep 60s

                if error_count > 10:
                    console.log("Too many consecutive errors, exiting")
                    return


if __name__ == "__main__":
    typer.run(retrieve_leads)
