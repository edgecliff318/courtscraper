import asyncio
import datetime
import json
import logging
import os
import random
import re
import time

import typer
from rich.console import Console
from rich.progress import track
from twilio.rest import Client

from src.core.config import get_settings
from src.models import leads as leads_model
from src.models import messages as messages_model
from src.scrapers import lexis
from src.scrapers.beenverified import BeenVerifiedScrapper
from src.scrapers.lexis import LexisNexisPhoneFinder
from src.services import cases as cases_service
from src.services import leads as leads_service
from src.services import messages as messages_service

console = Console()

logger = logging.getLogger()
settings = get_settings()

filters_keywords_include = [
    "speed",
    "alcohol",
    "driving",
    "expired",
    "insurance",
    "dwi",
    "trespass",
    "fail to stop",
    "assault",
    "possess",
    "disorderly conduct",
    "drove",
    "eluding",
    "excessive",
    "fail to obey",
    "fail to proceed",
    "fail to signal",
    "fail to yield",
    "fail to drive",
    "failed to drive",
    "failed to make",
    "failed to obey",
    "failed to stop",
    "failed to yield",
    "turning",
    "too closely",
    "improper lane use",
    "u-turn",
    "minor in possession",
    "miscellaneous moving violation",
    "miscellaneous weapon violation",
    "careless and imprudent manner",
    "oper a motor",
    "oper mtr",
    "operate motor",
    "operate vehicle",
    "pass vehicle",
    "red light violation",
    "resisting arrest",
]

filter_keyword_exclude = ["expired plates"]


def filter_leads(lead: leads_model.Lead):
    # If the lead.charges_description contains any of speed, alcohol, driving, expired, insurance
    # return True

    if lead.charges_description is None:
        return False

    for keyword in filter_keyword_exclude:
        if keyword in lead.charges_description.lower():
            return False

    for keyword in filters_keywords_include:
        if keyword in lead.charges_description.lower():
            return True

    return False


def remove_special_characters(text):
    if text is None:
        return ""
    return re.sub(r"[^a-zA-Z0-9]", " ", text)


def search_case(first_name, last_name, middle_name, dob, case_id):
    console.log(f"Searching for {first_name} {last_name} {dob}")

    # Check if the case already exists in the database
    leads_service_loader = leads_service.LeadsService()
    try:
        cases_search = leads_service_loader.get_items(
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            year_of_birth=dob,
        )
    except Exception as e:
        console.log(f"Error searching for {first_name} {last_name} {dob}")
        console.log(e)
        cases_search = None

    stop_search = False
    details = {}
    if cases_search is not None:
        for case_found in cases_search:
            if (
                case_found.case_id != case_id
                and case_found.status != "not_found"
                and case_found.status != "mailed"
                and case_found.status != "not_contacted_prioritized"
                and case_found.status != "not_valid"
                and case_found.status != "stop"
                and case_found.status != "contacted"
                and case_found.status != "wait"
                and case_found.phone is not None
            ):
                console.log(
                    f"Case {case_found.case_id} already exists with status {case_found.status}"
                )
                console.log(
                    f"Case details {case_found.first_name} {case_found.last_name} {case_found.year_of_birth} {case_found.charges_description}"
                )
                details = {
                    "status": "not_contacted_prioritized",
                    "phones": case_found.phones,
                    "email": case_found.email,
                    "phone": case_found.phone,
                    "report": case_found.report,
                    "lead_source": case_found.lead_source,
                }
                stop_search = True

    else:
        console.log(f"No case found for {first_name} {last_name} {dob}")
    return stop_search, details


def start_scrapper(
    source: str = "beenverified",
    username: str = None,
    password: str = None,
):
    if source == "beenverified":
        storage_state = os.path.join(
            settings.ROOT_PATH, "notebooks/playwright/.auth/state.json"
        )
        scraper = BeenVerifiedScrapper(storage_state=storage_state)
        console.log("Logged to BeenVerified")
    elif source == "lexis_nexis_phone_finder":
        storage_state = os.path.join(
            settings.ROOT_PATH,
            f"notebooks/playwright/.auth/lexis_{username}.json",
        )
        scraper = LexisNexisPhoneFinder(
            storage_state=storage_state, username=username, password=password
        )
        console.log("Logged to LexisNexis")
    return scraper


def retrieve_leads(
    source: str = "beenverified",
    username: str = None,
    password: str = None,
):
    asyncio.run(
        retrieve_leads_async(
            source=source, username=username, password=password
        )
    )


async def retrieve_leads_async(
    source: str = "beenverified",
    username: str = None,
    password: str = None,
):
    # Get all processing leads and change them to new
    # leads_processing = leads_service.get_leads(
    #     status="processing",
    #     start_date=datetime.datetime.now() - datetime.timedelta(days=10),
    # )

    # # Update all processing leads to new
    # leads_service.update_multiple_leads_status(
    #     [x.case_id for x in leads_processing], "new"
    # )

    # Get all failed leads and change them to new
    scraper = start_scrapper(source, username, password)

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    console.log("Logged to Twilio")

    error_count = 0

    while True:
        lead = leads_service.get_last_lead(status="prioritized")
        prioritized = True
        if lead is None:
            prioritized = False
            # lead = leads_service.get_last_lead(status="new")

        if lead is None:
            console.log("No new leads found")
            time.sleep(300)
            continue
        lock_service = leads_service.Lock()

        locked_items = lock_service.get_items()
        skip = False
        for locked_item_single in locked_items:
            if locked_item_single.case_id == lead.case_id:
                skip = True
                console.log(f"Lead {lead.case_id} is already locked")
                break
        if skip:
            continue

        lock_service.set_item(
            f"{source}_{username}",
            leads_model.Lock(case_id=lead.case_id, locked=True),
        )

        leads_service.update_lead_status(lead.case_id, "processing")

        if not filter_leads(lead) and not prioritized:
            leads_service.update_lead_status(lead.case_id, "not_prioritized")
            continue

        console.log(f"Found lead {lead.case_id}")

        case = cases_service.get_single_case(lead.case_id)

        try:
            lead_data = lead.model_dump()
            first_name = lead.first_name
            last_name = lead.last_name
            middle_name = case.middle_name or ""
            city = (
                case.address_city
                if case.address_city is not None
                else lead.city
            )
            if last_name is not None and len(last_name.split(" ")) > 1:
                middle_name = last_name.split(" ")[0]
                last_name = last_name.split(" ")[1]

            state = lead.state if lead.state is not None else "MO"

            dob = lead_data.get("year_of_birth")
            key = lead_data.get("case_id")

            # Get the case details from casenet

            state = lead_data["state"] or case.address_state_code or "MO"
            state = state.replace(" ", "")
            zip = lead_data["zip_code"] or case.address_zip or ""
            address_line1 = lead_data["address"] or case.address_line_1 or ""
            address_line2 = ""

            first_name = remove_special_characters(first_name)
            last_name = remove_special_characters(last_name)
            middle_name = remove_special_characters(middle_name)
            city = remove_special_characters(city)
            address_line1 = remove_special_characters(address_line1)
            address_line2 = remove_special_characters(address_line2)

            # Check if the case already exists in the database
            stop_search, details = search_case(
                first_name, last_name, middle_name, dob, key
            )

            if stop_search:
                leads_service.patch_lead(case_id=key, **details)
                continue

            try:
                if source == "beenverified":
                    data = await scraper.search_person(
                        first_name=first_name,
                        last_name=last_name,
                        middle_name=middle_name,
                        age=case.age,
                        city=city,
                        state=state,
                    )

                elif source == "lexis_nexis_phone_finder":
                    data = await scraper.search_person(
                        first_name=first_name,
                        last_name=last_name,
                        middle_name=middle_name,
                        dob=dob,
                        age=case.age,
                        city=city,
                        state=state,
                        zip=zip,
                        address_line1=address_line1,
                        address_line2=address_line2,
                    )
                if hasattr(scraper, "close"):
                    await scraper.close()
            except Exception as e:
                console.log("An issue happened with the scraper")
                if hasattr(scraper, "close"):
                    await scraper.close()
                raise e
            if data is None:
                console.log(
                    f"No lead for {lead.case_id} found on BeenVerified"
                )
                lead_data["status"] = "not_found"
                leads_service.patch_lead(
                    case_id=lead.case_id,
                    status="not_found",
                    lead_source=source,
                )
                continue
            lead_data.update(data)
            lead_data["status"] = (
                "not_contacted" if not prioritized else "not_contacted"
            )

            if lead_data["phone"] is None or len(lead_data["phone"]) == 0:
                phone_transformed = {}
                lead_data["status"] = "not_found"
            else:
                phone_transformed = {}
                for lead_phone_id, lead_phone in lead_data["phone"].items():
                    try:
                        phone = client.lookups.phone_numbers(
                            lead_phone.get("phone")
                        ).fetch(type="carrier")
                    except Exception as e:
                        logger.error(
                            f"Error retrieving phone {lead_phone.get('phone')}"
                        )
                        continue
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
                        phone_transformed[lead_phone_id]["carrier"] = (
                            phone.carrier["type"]
                        )

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
            lead_data["phones"] = [
                p["phone"] for p in lead_data["phone"].values()
            ]
            lead_data["lead_source"] = source

            leads_service.insert_lead(leads_model.Lead(**lead_data))
            console.log(f"Lead {lead.case_id} retrieved successfully ✅")
            # Wait a random time between 30 seconds and 5 minutes
            if source == "beenverified":
                waiting_time = random.randint(15, 30)
            else:
                waiting_time = 0

            console.log(f"Waiting {waiting_time} seconds before next lead")
            time.sleep(waiting_time)
            error_count = 0
        except Exception as e:
            logger.error(f"Error retrieving lead {lead.case_id} - {e}")
            console.log(f"Error retrieving lead {lead.case_id} - {e}")
            error_count += 1

            if error_count > 20:
                console.log("Too many consecutive errors, exiting")
                return


def get_default_dates():
    """Get default from_date and to_date values."""
    from_date = (
        datetime.datetime.now() - datetime.timedelta(days=1)
    ).strftime("%Y-%m-%d")
    to_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    return from_date, to_date


def process_inbound_message(message):
    """Process inbound Twilio messages."""
    lead = leads_service.get_lead_by_phone(message.from_)
    if not lead:
        console.log(f"Lead not found with phone {message.from_}")
        return

    # Check if interaction exists
    if messages_service.get_single_interaction(message.sid):
        console.log(f"Interaction {message.sid} already exists")
        # If needed, update the interaction here
        return

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

    messages_service.insert_interaction(interaction)

    # Update lead status based on message content
    if "yes" in message.body.lower():
        leads_service.update_lead_status(lead.case_id, "yes")
    elif "stop" in message.body.lower():
        leads_service.update_lead_status(lead.case_id, "stop")
    else:
        leads_service.update_lead_status(lead.case_id, "responded")


def process_outbound_message(message):
    """Process outbound Twilio messages."""
    lead = leads_service.get_lead_by_phone(message.to)
    if not lead:
        console.log(f"Lead not found with phone {message.to}")
        return

    if message.status not in ["delivered", "sent"]:
        if lead.status == "not_contacted":
            leads_service.update_lead_status(lead.case_id, "failed")
    elif lead.status == "not_contacted":
        leads_service.update_lead_status(lead.case_id, "contacted")


def sync_twilio(from_date: str = None, to_date: str = None):
    """Sync messages from Twilio."""
    messages_twilio = get_twilio_messages(from_date, to_date)

    for message in track(messages_twilio):
        if not hasattr(message, "from_"):
            console.log(f"Message {message.sid} has no _from attribute")
            continue

        if message.direction == "inbound":
            process_inbound_message(message)
        elif "outbound" in str(message.direction).lower():
            process_outbound_message(message)


def get_twilio_messages(from_date: str = None, to_date: str = None):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    if not from_date or not to_date:
        from_date, to_date = get_default_dates()

    messages_twilio = client.messages.list(
        date_sent_after=from_date, date_sent_before=to_date
    )

    return messages_twilio


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
