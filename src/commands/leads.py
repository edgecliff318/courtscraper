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


def filter_leads(lead: leads_model.Lead):
    # If the lead.charges_description contains any of speed, alcohol, driving, expired, insurance
    # return True
    if lead.charges_description is None:
        return False
    if "speed" in lead.charges_description.lower():
        return True
    if "alcohol" in lead.charges_description.lower():
        return True
    if "driving" in lead.charges_description.lower():
        return True
    if "expired" in lead.charges_description.lower():
        return True
    if "insurance" in lead.charges_description.lower():
        return True
    return False


def retrieve_leads():
    # Wait 2 hours before starting the process
    logger.info("Waiting 2 hours before starting the process")
    scrapper = BeenVerifiedScrapper(cache=False)
    console.print("Logged to BeenVerified")
    while True:
        leads = leads_service.get_leads(status="new")
        # Order leads by case_date
        leads = [
            lead_single for lead_single in leads if filter_leads(lead_single)
        ]
        leads = sorted(leads, key=lambda x: x.case_date, reverse=True)
        error_count = 0
        for lead in leads:
            try:
                lead_data = lead.dict()
                first_name = lead.first_name
                last_name = lead.last_name
                middle_name = None
                if len(last_name.split(" ")) > 1:
                    middle_name = last_name.split(" ")[0]
                    last_name = last_name.split(" ")[1]
                link = scrapper.get_beenverified_link(
                    first_name=first_name,
                    last_name=last_name,
                    middle_name=middle_name,
                    year=lead.year_of_birth,
                )
                data = scrapper.retrieve_information(link)
                if data.get("exact_match") is False:
                    console.log(
                        f"Lead {lead.case_id} not found in BeenVerified"
                    )
                    waiting_time = random.randint(30, 150)
                    console.log(
                        f"Waiting {waiting_time} seconds before next lead"
                    )
                    lead_data["status"] = "not_found"
                    leads_service.insert_lead(leads_model.Lead(**lead_data))
                    time.sleep(waiting_time)
                    continue
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
                logger.error(f"Error retrieving lead {lead.case_id} - {e}")
                console.log(f"Error retrieving lead {lead.case_id} - {e}")
                error_count += 1
                # Sleep 60s
                try:
                    scrapper.driver.save_screenshot(
                        f"error_{lead.case_id}.png"
                    )
                except Exception:
                    # Restarting the driver
                    console.log("Restarting the driver")
                    scrapper = BeenVerifiedScrapper(cache=False)

                if error_count > 20:
                    console.log("Too many consecutive errors, exiting")
                    return


if __name__ == "__main__":
    typer.run(retrieve_leads)
