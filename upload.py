import requests

from src.core.config import get_settings
from src.services.leads import get_last_lead

settings = get_settings()


def add_lead(lead):
    # Add lead as a contact to CloudTalk
    url = "https://my.cloudtalk.io/api/"
    payload = {
        "name": f"{lead.first_name}, {lead.middle_name}, {lead.last_name}",
        "ContactNumber": [
            {
                "public_number": phone,
            }
            for phone in lead.phones
        ],
        "ContactAttribute": [
            {
                "attribute_id": 5723,
                "value": lead.age,
            },
            {"attribute_id": 5725, "value": lead.charges_description},
            {"attribute_id": 5727, "value": lead.source},
            {"attribute_id": 5729, "value": lead.case_id},
        ],
    }
    headers = {
        "Content-Type": "application/json",
    }

    # Get contacts
    contacts = requests.get(
        url + "contacts/index.json",
        headers=headers,
        auth=(settings.CLOUDTALK_API_KEY, settings.CLOUDTALK_API_SECRET),
    )

    contacts = contacts.json().get("responseData").get("data")

    # Check if contact already exists
    for contact in contacts:
        if (
            contact.get("Contact").get("name")
            == f"{lead.first_name}, {lead.middle_name}, {lead.last_name}"
        ):
            print("Contact already exists")
            return

    response = requests.request(
        "PUT",
        url + "contacts/add.json",
        headers=headers,
        json=payload,
        auth=(settings.CLOUDTALK_API_KEY, settings.CLOUDTALK_API_SECRET),
    )

    if response.status_code == 201:
        print(f"Contact added for {payload.get('name')}")

    else:
        print("Error")
        print(response.status_code)
        print(response.text)


if __name__ == "__main__":
    leads_list = get_last_lead(
        court_code_list="temp",
        status="not_contacted",
        limit=50,
        search_limit=1000,
    )
    for lead in leads_list:
        add_lead(lead)
