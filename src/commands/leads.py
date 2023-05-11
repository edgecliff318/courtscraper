import logging
import random
import time

import typer
from rich.console import Console

from src.models import leads as leads_model
from src.scrapers.beenverified import BeenVerifiedScrapper
from src.services import leads as leads_service

console = Console()

logger = logging.getLogger()


def retrieve_leads():
    scrapper = BeenVerifiedScrapper(cache=False)
    console.print("Logged to BeenVerified")
    while True:
        leads = leads_service.get_leads(status="new")
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
                # Wait a random time between 30 seconds and 5 minutes
                waiting_time = random.randint(30, 300)
                console.log(f"Waiting {waiting_time} seconds before next lead")
                time.sleep(waiting_time)
                error_count = 0
            except Exception as e:
                scrapper.driver.save_screenshot(f"error_{lead.case_id}.png")
                logger.error(f"Error retrieving lead {lead.case_id} - {e}")
                console.log(f"Error retrieving lead {lead.case_id} - {e}")
                error_count += 1
                # Sleep 60s

                if error_count > 10:
                    console.log("Too many consecutive errors, exiting")
                    return


if __name__ == "__main__":
    typer.run(retrieve_leads)
