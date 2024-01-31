from datetime import datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from src.core.config import get_settings
from src.services import cases as cases_service
from src.services import leads as leads_service

settings = get_settings()


def add_lead_cloud_talk(lead):
    # Add lead as a contact to CloudTalk
    url = "https://my.cloudtalk.io/api/"

    headers = {
        "Content-Type": "application/json",
    }

    case = cases_service.get_single_case(lead.case_id)
    tag = mapping(lead.charges_description)

    for phone_id, phone in enumerate(lead.phones):
        source = lead.source if lead.source is not None else case.location
        case_date = (
            case.case_date.strftime("%Y-%m-%d")
            if case.case_date is not None
            else "None"
        )

        if case.arrest_date is not None:
            case_date = case.arrest_date.strftime("%Y-%m-%d")
        elif case.charges is not None and len(case.charges) > 0:
            case_charge = case.charges[0]

            if case_charge.get("charge_filingdate") is not None:
                case_date = case_charge.get("charge_filingdate")
            elif case_charge.get("offense_date") is not None:
                case_date = case_charge.get("offense_date")
            else:
                case_date = "None"
            # Update format
            if case_date != "None":
                case_date = datetime.strptime(case_date, "%m/%d/%Y").strftime(
                    "%Y-%m-%d"
                )

        case_location = (
            case.where_held if case.where_held is not None else case.location
        )
        payload = {
            "name": f"{lead.first_name}, {lead.middle_name}, {lead.last_name} - {phone_id}",
            "company": f"{tag.upper()} - {case_location} - {case_date}"[:254],
            "ContactNumber": [
                {
                    "public_number": phone,
                }
            ],
            "ContactsTag": [{"name": "leads"}, {"name": tag}],
            "ContactAttribute": [
                {
                    "attribute_id": 5723,
                    "value": lead.age,
                },
                {
                    "attribute_id": 5725,
                    "value": lead.charges_description[:254],
                },
                {
                    "attribute_id": 5727,
                    # Value should be 255 or less
                    "value": (
                        f"Source {source} - Arrested at {case.arrest_time if case.arrest_time is not None else None} "
                        f"on {case_date}"
                    )[:254],
                },
                {"attribute_id": 5729, "value": lead.case_id},
                {
                    "attribute_id": 5739,
                    "value": case_location,
                },
                {
                    "attribute_id": 5741,
                    "value": case_date,
                },
            ],
        }

        response = requests.request(
            "PUT",
            url + "contacts/add.json",
            headers=headers,
            json=payload,
            auth=(settings.CLOUDTALK_API_KEY, settings.CLOUDTALK_API_SECRET),
        )

        if response.status_code == 201 or response.status_code == 200:
            print(f"Contact added for {payload.get('name')}")
            leads_service.patch_lead(lead.case_id, cloudtalk_upload=True)

        else:
            print("Error")
            print(response.status_code)
            print(response.text)


def add_website_lead(lead: dict, tag=None):
    url = "https://my.cloudtalk.io/api/"

    headers = {
        "Content-Type": "application/json",
    }

    if tag is None:
        tag = "website"

    creation_date = lead["creation_date"]

    payload = {
        "name": f"{lead['state']} - {lead['court']} - {creation_date}"[:254],
        "company": f"{tag.upper()} - {lead['court']} - {creation_date}"[:254],
        "ContactNumber": [
            {
                "public_number": lead.get("phone"),
            }
        ],
        "ContactsTag": [{"name": "leads"}, {"name": tag}],
        "ContactAttribute": [
            {
                "attribute_id": 5725,
                "value": lead.get("violation", "")[:254]
                if lead.get("violation") is not None
                else "",
            },
            {
                "attribute_id": 5739,
                "value": f"{lead.get('state')} - {lead.get('court')}"[:254],
            },
            {
                "attribute_id": 5741,
                "value": creation_date,
            },
        ],
    }

    response = requests.request(
        "PUT",
        url + "contacts/add.json",
        headers=headers,
        json=payload,
        auth=(settings.CLOUDTALK_API_KEY, settings.CLOUDTALK_API_SECRET),
    )

    if response.status_code == 201:
        print(f"Contact added for {payload.get('name')}")
        leads_service.patch_lead(lead.case_id, cloudtalk_upload=True)

    else:
        print("Error")
        print(response.status_code)
        print(response.text)


def process_redudant_numbers():
    url = "https://my.cloudtalk.io/api/"

    headers = {
        "Content-Type": "application/json",
    }

    print("Getting contacts")

    contacts = requests.request(
        "GET",
        url + "contacts/index.json",
        headers=headers,
        auth=(settings.CLOUDTALK_API_KEY, settings.CLOUDTALK_API_SECRET),
        params={"limit": 1000, "tag": "leads"},
    )

    contacts_json = contacts.json()

    pages = contacts_json.get("responseData").get("pageCount")
    current_page = contacts_json.get("responseData").get("pageNumber")

    contacts_list = contacts_json.get("responseData").get("data")

    while current_page <= pages:
        print(f"Getting page {current_page}")
        current_page += 1
        contacts = requests.request(
            "GET",
            url + "contacts/index.json",
            headers=headers,
            auth=(settings.CLOUDTALK_API_KEY, settings.CLOUDTALK_API_SECRET),
            params={"limit": 1000, "tag": "leads", "page": current_page},
        )
        contacts_json = contacts.json()
        contacts_list += contacts_json.get("responseData").get("data")

    print(f"Found {len(contacts_list)} contacts")
    contacts_by_phone = {}

    for contact in contacts_list:
        phone = contact.get("ContactNumber").get("public_number")

        if phone not in contacts_by_phone.keys():
            contacts_by_phone[phone] = []

        contacts_by_phone[phone].append(contact)

    contacts_by_tag_order = {
        "website": 6,
        "dwi": 5,
        "major": 4,
        "minor": 3,
        "leads": 2,
        "other": 1,
    }

    retry_strategy = Retry(
        total=3,
        status_forcelist=[429],
        method_whitelist=["GET"],
        backoff_factor=2,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    for phone, contacts_items in contacts_by_phone.items():
        if len(contacts_items) > 1:
            print(f"Found {len(contacts_items)} contacts for {phone}")
            # Get the tags for each contact and keep the one with the highest priority tag
            contact_order = {}
            for contact in contacts_items:
                contact_full = http.request(
                    "GET",
                    url + f"contacts/show/{contact.get('Contact').get('id')}.json",
                    headers=headers,
                    auth=(
                        settings.CLOUDTALK_API_KEY,
                        settings.CLOUDTALK_API_SECRET,
                    ),
                )

                contact_order[contact.get("Contact").get("id")] = 0
                tags = contact_full.json().get("responseData").get("Tag")
                print(f"Tags for {contact.get('Contact').get('name')}: {tags}")
                for tag in tags:
                    if tag.get("name") in contacts_by_tag_order.keys():
                        contact_order[contact.get("Contact").get("id")] = {
                            "order": contacts_by_tag_order.get(tag.get("name")),
                            "tag": tag.get("name"),
                        }

            # Get the contact with the highest priority tag
            contact_to_keep = max(
                contact_order, key=lambda x: contact_order[x].get("order")
            )

            # Delete the other contacts
            for contact_id, contact_summary in contact_order.items():
                if contact_order != contact_to_keep:
                    print(f"Deleting contact {contact_id}")
                    response = requests.request(
                        "DELETE",
                        url + f"contacts/delete/{contact_id}.json",
                        headers=headers,
                        auth=(
                            settings.CLOUDTALK_API_KEY,
                            settings.CLOUDTALK_API_SECRET,
                        ),
                    )

                    if response.status_code == 200:
                        print(f"Contact {contact_id} deleted")
                    else:
                        print(f"Error deleting contact {contact_id}")
                        print(response.text)

                    # Add the tag to the contact to keep
                    print(
                        f"Adding tag {contact_summary.get('tag')} to {contact_to_keep}"
                    )
                    # https://my.cloudtalk.io/api/contacts/addTags/{contactId}.json
                    requests.request(
                        "PUT",
                        url + f"contacts/addTags/{contact_to_keep}.json",
                        headers=headers,
                        auth=(
                            settings.CLOUDTALK_API_KEY,
                            settings.CLOUDTALK_API_SECRET,
                        ),
                        json={"tags": [contact_summary.get("tag")]},
                    )


def mapping(charges):
    if charges is None:
        raise ValueError("Charges cannot be None")
    if (
        "intox" in charges.lower()
        or "alcohol" in charges.lower()
        or "dui" in charges.lower()
        or "dwi" in charges.lower()
        or "drunk" in charges.lower()
    ):
        output = "dwi"

    elif (
        "20-25 mph over" in charges.lower()
        or "careless" in charges.lower()
        or "imprudent" in charges.lower()
        or "license" in charges.lower()
        or "insurance" in charges.lower()
    ):
        output = "major"

    elif "19" in charges.lower():
        output = "minor"

    elif "mph" in charges.lower():
        output = "minor"

    else:
        return "other"

    print(f"{charges} mapped to {output}")
    return output


def fetch_call_history(date_from, date_to):
    url = "https://my.cloudtalk.io/api/"
    headers = {"Content-Type": "application/json"}

    params = {
        "date_from": date_from.strftime("%Y-%m-%d %H:%M:%S"),
        "date_to": date_to.strftime("%Y-%m-%d %H:%M:%S"),
    }

    response = requests.request(
        "GET",
        url + "calls/index.json",
        headers=headers,
        auth=(settings.CLOUDTALK_API_KEY, settings.CLOUDTALK_API_SECRET),
        params=params,
    )

    calls_json = response.json()
    pages = calls_json.get("responseData").get("pageCount")
    current_page = calls_json.get("responseData").get("pageNumber")

    calls_list = [
        call.get("Cdr") for call in calls_json.get("responseData").get("data")
    ]

    while current_page < pages:
        print(f"Getting page {current_page + 1}")
        current_page += 1
        response = requests.request(
            "GET",
            url + "calls/index.json",
            headers=headers,
            auth=(settings.CLOUDTALK_API_KEY, settings.CLOUDTALK_API_SECRET),
            params={**params, "page": current_page},
        )
        calls_json = response.json()
        calls_list += [
            call.get("Cdr") for call in calls_json.get("responseData").get("data")
        ]

    return calls_list
