import datetime
import json
import logging
import random
import time

import typer
from rich.console import Console
from rich.progress import track
from twilio.rest import Client

from src.core.config import get_settings
from src.models import leads as leads_model
from src.models import messages as messages_model
from src.scrapers.beenverified import BeenVerifiedScrapper, CaptchaException
from src.services import cases as cases_service
from src.services import leads as leads_service
from src.services import messages as messages_service

console = Console()

logger = logging.getLogger()
settings = get_settings()


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
    # Get all processing leads and change them to new

    leads_processing = leads_service.get_leads(status="processing")

    leads_service.update_multiple_leads_status(
        [x.case_id for x in leads_processing], "new"
    )

    scrapper = BeenVerifiedScrapper(cache=False)
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    console.print("Logged to BeenVerified")

    error_count = 0

    while True:
        lead = leads_service.get_last_lead(status="new")

        if lead is None:
            console.log("No new leads found")
            time.sleep(300)
            continue

        if not filter_leads(lead):
            leads_service.update_lead_status(lead.case_id, "not_prioritized")
            continue

        leads_service.update_lead_status(lead.case_id, "processing")
        case = cases_service.get_single_case(lead.case_id)

        try:
            lead_data = lead.model_dump()
            first_name = lead.first_name
            last_name = lead.last_name
            middle_name = case.middle_name
            city = case.address_city
            if last_name is not None and len(last_name.split(" ")) > 1:
                middle_name = last_name.split(" ")[0]
                last_name = last_name.split(" ")[1]
            link = scrapper.get_beenverified_link(
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                year=lead.year_of_birth,
                city=city,
            )
            try:
                data = scrapper.retrieve_information(link)
            except CaptchaException:
                continue
            if data is None:
                console.log(
                    f"Error processing lead {lead.case_id} on BeenVerified"
                )
                waiting_time = random.randint(15, 30)
                console.log(f"Waiting {waiting_time} seconds before next lead")
                lead_data["status"] = "processing_error"
                leads_service.insert_lead(leads_model.Lead(**lead_data))
                time.sleep(waiting_time)
                continue
            if data.get("exact_match") is False:
                console.log(f"Lead {lead.case_id} not found in BeenVerified")
                waiting_time = random.randint(15, 30)
                console.log(f"Waiting {waiting_time} seconds before next lead")
                lead_data["status"] = "not_found"
                leads_service.insert_lead(leads_model.Lead(**lead_data))
                time.sleep(waiting_time)
                continue

            lead_data["phone"] = data.get("phone")
            lead_data["details"] = data.get("details")
            lead_data["email"] = json.loads(json.dumps(data.get("email")))
            lead_data["address"] = json.loads(json.dumps(data.get("address")))
            lead_data["status"] = "not_contacted"
            lead_data["report"] = json.loads(json.dumps(data.get("report")))

            if lead_data["phone"] is None or len(lead_data["phone"]) == 0:
                phone_transformed = {}
                lead_data["status"] = "not_found"
            else:
                phone_transformed = {}
                for lead_phone_id, lead_phone in lead_data["phone"].items():
                    if lead_phone.get("meta", {}).get("confidence", 0) < 70:
                        continue
                    phone = client.lookups.phone_numbers(
                        lead_phone.get("number")
                    ).fetch(type="carrier")
                    phone_transformed[lead_phone_id] = lead_phone
                    phone_transformed[lead_phone_id][
                        "phone"
                    ] = phone.phone_number
                    if phone is None:
                        console.log(
                            f"Phone {lead_phone.get('number')} not found in Twilio"
                        )
                        phone_transformed[lead_phone_id][
                            "status"
                        ] = "not_valid"
                    if phone.carrier is not None:
                        phone_transformed[lead_phone_id][
                            "carrier"
                        ] = phone.carrier["type"]

                        phone_transformed[lead_phone_id].update(phone.carrier)
                        if (
                            phone.carrier["type"] == "landline"
                            or phone.carrier["type"] == "voip"
                        ):
                            phone_transformed[lead_phone_id][
                                "status"
                            ] = "not_valid"
                        else:
                            phone_transformed[lead_phone_id][
                                "phone"
                            ] = phone.phone_number
                            phone_transformed[lead_phone_id][
                                "status"
                            ] = "valid"

            # Check if all phone has not_valid status set the lead status to not_valid
            if all(
                phone.get("status") == "not_valid"
                for phone in phone_transformed.values()
            ):
                lead_data["status"] = "not_valid"

            lead_data["phone"] = json.loads(json.dumps(phone_transformed))

            leads_service.insert_lead(leads_model.Lead(**lead_data))
            console.log(f"Lead {lead.case_id} retrieved")
            # Wait a random time between 30 seconds and 5 minutes
            waiting_time = random.randint(15, 30)
            console.log(f"Waiting {waiting_time} seconds before next lead")
            time.sleep(waiting_time)
            error_count = 0
        except Exception as e:
            logger.error(f"Error retrieving lead {lead.case_id} - {e}")
            console.log(f"Error retrieving lead {lead.case_id} - {e}")
            error_count += 1
            # Sleep 60s
            try:
                scrapper.driver.save_screenshot(f"error_{lead.case_id}.png")
            except Exception:
                # Restarting the driver
                console.log("Restarting the driver")
                scrapper = BeenVerifiedScrapper(cache=False)

            if error_count > 20:
                console.log("Too many consecutive errors, exiting")
                return


def sync_twilio(from_date: str = None, to_date: str = None):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    if from_date is None:
        # Today
        from_date = (
            datetime.datetime.now() - datetime.timedelta(days=1)
        ).strftime("%Y-%m-%d")

    if to_date is None:
        # Tomorrow
        to_date = (
            datetime.datetime.now() + datetime.timedelta(days=1)
        ).strftime("%Y-%m-%d")

    # Get messages from Twilio
    messages_twilio = client.messages.list(
        date_sent_after=from_date, date_sent_before=to_date
    )

    for message in track(messages_twilio):
        # If Inbound message:
        #   - Get the lead
        #   - Update the lead with the message
        #   - Update the lead status to contacted
        if not hasattr(message, "from_"):
            console.log(f"Message {message.sid} has no _from attribute")
            continue
        if message.direction == "inbound":
            lead = leads_service.get_lead_by_phone(message.from_)
            if lead is None:
                console.log(f"Lead not found with phone {message.from_}")
                continue
            # Add interaction

            interaction = messages_model.Interaction(
                case_id=lead.case_id,
                message=message.body,
                type="sms",
                status=message.status,
                id=message.sid,
                creation_date=message.date_sent,
                direction=message.direction,
                phone=message.from_,
            )

            if (
                messages_service.get_single_interaction(message.sid)
                is not None
            ):
                console.log(f"Interaction {message.sid} already exists")
                messages_service.update_interaction(interaction)
                continue

            messages_service.insert_interaction(interaction)

            if message.body is not None and "yes" in message.body.lower():
                leads_service.update_lead_status(lead.case_id, "yes")
            elif "stop" in message.body.lower():
                leads_service.update_lead_status(lead.case_id, "stop")
            else:
                leads_service.update_lead_status(lead.case_id, "responded")

        elif "outbound" in str(message.direction).lower():
            # Check the status of the message
            # If delivered, update the status of the interaction to delivered
            # If failed, update the status of the interaction to failed
            lead = leads_service.get_lead_by_phone(message.to)

            if lead is None:
                console.log(f"Lead not found with phone {message.to}")
                continue

            if message.status != "delivered" and message.status != "sent":
                if lead.status == "not_contacted":
                    leads_service.update_lead_status(lead.case_id, "failed")
            elif lead.status == "not_contacted":
                leads_service.update_lead_status(lead.case_id, "contacted")


def analyze_leads():
    console.log("Loading leads")
    leads = leads_service.get_leads(status="contacted")
    console.log("Initializing twilio")
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    for lead in track(leads):
        # Use Twilio Lookup to get the carrier
        # If land line or voip, update the lead status to not_prioritized
        if lead.phone is None:
            continue

        if "no phone" in lead.phone.lower():
            leads_service.update_lead_status(lead.case_id, "not_found")
            continue

        if lead.carrier is not None and "+" in lead.phone:
            continue

        phone = client.lookups.phone_numbers(lead.phone).fetch(type="carrier")

        if phone is None:
            console.log(f"Phone {lead.phone} not found in Twilio")
            leads_service.update_lead_status(lead.case_id, "not_prioritized")
            continue
        if phone.carrier is not None:
            if (
                phone.carrier["type"] == "landline"
                or phone.carrier["type"] == "voip"
            ):
                lead.status = "not_prioritized"
            lead.carrier = phone.carrier["type"]
        if phone.caller_name is not None:
            continue
        lead.phone = phone.phone_number
        leads_service.update_lead(lead)


if __name__ == "__main__":
    typer.run(retrieve_leads)
