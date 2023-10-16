import datetime
import json
import logging

import requests
from bs4 import BeautifulSoup

from src.models.cases import Case
from src.models.leads import Lead

logger = logging.getLogger(__name__)


class MyCase:
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password
        self.session = requests.Session()

    def login(self):
        # Refresh the headers
        url = "https://auth.mycase.com/login_sessions?client_id=tCEM8hNY7GaC2c8P&response_type=code"
        # TODO: #17 Move the login details to Firebase
        payload = "utf8=%E2%9C%93&login_session%5Bemail%5D=shawn%40tickettakedown.com&login_session%5Bpassword%5D=MASdorm2023!!"
        headers = {
            "authority": "auth.mycase.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/x-www-form-urlencoded",
            "dnt": "1",
            "origin": "https://www.mycase.com",
            "pragma": "no-cache",
            "referer": "https://www.mycase.com/",
            "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-site",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        }
        response = self.session.request(
            "POST", url, headers=headers, data=payload
        )

        if response.status_code != 200:
            raise Exception("Could not log into MyCase")

        # Get the CSRF token
        response = self.session.request(
            "GET", "https://meyer-attorney-services.mycase.com/dashboard"
        )

        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.find("meta", {"name": "csrf-token"})["content"]
        headers.update(
            {
                "x-csrf-token": str(csrf_token),
                # "cookie": response.headers["Set-Cookie"],
                "authority": "meyer-attorney-services.mycase.com",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "content-type": "application/json",
                "dnt": "1",
                "origin": "https://meyer-attorney-services.mycase.com",
                "pragma": "no-cache",
                "referer": "https://meyer-attorney-services.mycase.com/dashboard",
                "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                "x-requested-with": "XMLHttpRequest",
            }
        )
        self.session.headers.update(headers)

    def add_contact(self, lead: Lead, case: Case):
        url = (
            "https://meyer-attorney-services.mycase.com/contacts/clients.json"
        )

        payload = json.dumps(
            {
                "web_view": True,
                "adding_contact_group": 0,
                "client": {
                    "first_name": lead.first_name,
                    "middle_initial": lead.middle_name,
                    "last_name": lead.last_name,
                    "email": lead.email,
                    "contact_group_id": "1477683",
                    "contact_group_name": "",
                    "login_enabled": "false",
                    "cell_phone": lead.phone,
                    "lead_id": "",
                    "address_attributes": {
                        "street": case.address_line_1,
                        "city": case.address_city,
                        "state": case.address_state_code,
                        "zip_code": case.address_zip,
                        "country": "US",
                    },
                    "timezone": "America/Chicago",
                    "birthday": case.birth_date,
                    "companies": [],
                    "custom_field_values_attributes": {
                        "0": {"value": "", "custom_field_id": "752476"},
                        "1": {"value": "", "custom_field_id": "752480"},
                        "2": {"value": "", "custom_field_id": "752482"},
                        "3": {"value": "", "custom_field_id": "752483"},
                        "4": {"value": "", "custom_field_id": "752484"},
                        "5": {"value": "", "custom_field_id": "752485"},
                        "6": {"value": "", "custom_field_id": "752486"},
                    },
                },
            }
        )

        response = self.session.request("POST", url, data=payload)

        response_json = response.json()
        response_status = response_json.get("success")
        response_client = response_json.get("client", {}).get("id")

        if response_status is not True:
            logger.error(response.text)
            raise Exception(
                f"Could not add contact to MyCase"
                f" {response_status} - {response_json.get('object_errors', {}).get('full_messages', '')}"
            )

        return response_client

    def get_case_custom_fields(self):
        url = "https://meyer-attorney-services.mycase.com/custom_fields.json?filter=court_case"
        response = self.session.request("GET", url)
        return response.json()

    def validate_case(self, payload_dict):
        url = "https://meyer-attorney-services.mycase.com/court_cases/validate_case.json"

        payload = json.dumps(payload_dict)

        response = self.session.request("POST", url, data=payload)

        return response.status_code, response.text

    def add_case(self, lead: Lead, case: Case, client_id: str):
        custom_fields = self.get_case_custom_fields()
        url = "https://meyer-attorney-services.mycase.com/court_cases"

        today = datetime.datetime.now()
        # Format in US date format
        today = today.strftime("%m/%d/%Y")
        court_date = ""
        court_time = ""
        if case.dockets is not None:
            for docket in case.dockets:
                if "initial" in docket.get("docket_desc", "").lower():
                    # Get the associated_docketscheduledinfo
                    schedule = docket.get("associated_docketscheduledinfo", {})
                    if isinstance(schedule, list):
                        schedule = schedule.pop()
                    court_date = schedule.get("associated_date", "")
                    court_time = schedule.get("associated_time", "")
                    break

        # Selecting the county
        country_custom_field = [
            field for field in custom_fields if field.get("id") == "568026"
        ]
        if len(country_custom_field) == 0 or case.location is None:
            county = ""
        else:
            country_custom_field = country_custom_field.pop()
            county_candidate = [
                c
                for c in country_custom_field.get("list_options", [])
                if case.location.lower() in c.lower()
            ]
            if len(county_candidate) == 0:
                county = ""
            else:
                county = county_candidate.pop().get("option_value")

        # Selecting the charges
        charges_custom_field = [
            field for field in custom_fields if field.get("id") == "561060"
        ]

        if len(charges_custom_field) == 0 or lead.charges_description is None:
            charges = "Other"
            charges_text = ""

        else:
            charges_text = lead.charges_description
            charges_custom_field = charges_custom_field.pop()
            charges_candidate = [
                c
                for c in charges_custom_field.get("list_options", [])
                if lead.charges_description.lower() in c.lower()
            ]
            if len(charges_candidate) == 0:
                charges = "Other"
            else:
                charges = charges_candidate.pop().get("option_value")

        payload_dict = {
            "has_new_company": False,
            "has_existing_company": False,
            "court_case": {
                "name": (
                    f"{lead.last_name} {lead.middle_name}"
                    f" {lead.first_name}  - {case.location}"
                    f" - {case.case_id}"
                ),
                "case_number": case.case_id,
                "date_opened": today,
                "practice_area_id": "4164778",
                "practice_area_name": "",
                "case_stage": "751968",
                "flat_fee": "",
                "description": "",
                "billing_user_id": client_id,
                "billing_type": "",
                "sol_date": "",
                "use_sol_reminders": "0",
                "conflict_checks_attributes": [
                    {"completed": False, "note": ""}
                ],
                "ledes_enabled": False,
                "ledes_information_attributes": {},
                "office_id": "250854",
                "sol_reminders": [],
                "custom_field_values_attributes": {
                    "0": {
                        "value": case.location,
                        "custom_field_id": "552480",
                    },
                    "1": {
                        "value": "CIRCUIT"
                        if (
                            case.court_type is not None
                            and (
                                "circ" in case.court_type.lower()
                                or case.court_type.lower() == "c"
                            )
                        )
                        else "MUNICIPAL",
                        "custom_field_id": "552482",
                    },
                    "2": {
                        "value": court_date,
                        "custom_field_id": "552496",
                    },
                    "3": {
                        "value": "Counsel is waiting for discovery",
                        "custom_field_id": "552499",
                    },
                    "4": {
                        "value": court_time,
                        "custom_field_id": "552501",
                    },
                    "5": {
                        "value": case.judge.get("formatted_name")
                        if case.judge is not None
                        else "",
                        "custom_field_id": "552502",
                    },
                    "6": {
                        "value": charges,
                        "custom_field_id": "561060",
                    },
                    "7": {"value": "", "custom_field_id": "561063"},
                    "8": {"value": "", "custom_field_id": "561643"},
                    "9": {
                        "value": case.fine.get("total_amount", "")
                        if case.fine is not None
                        else "",
                        "custom_field_id": "561644",
                    },
                    "10": {"value": "", "custom_field_id": "561645"},
                    "11": {
                        "value": county,
                        "custom_field_id": "568026",
                    },
                    "12": {"value": "", "custom_field_id": "573938"},
                    "13": {"value": "N", "custom_field_id": "573959"},
                    "14": {"value": "", "custom_field_id": "599749"},
                    "15": {"value": charges_text, "custom_field_id": "814435"},
                },
            },
            "adding_practice_area": False,
            "lawyers": {
                "27081302": "Default Rate",
                "27310503": "Default Rate",
            },
            "rates": {"27081302": None, "27310503": None},
            "existing_clients": [client_id],
            "lead_lawyer_id": None,
            "originating_lawyer_id": None,
        }

        payload = json.dumps(payload_dict)

        validate_case_status, validate_case_response = self.validate_case(
            payload_dict
        )
        if validate_case_status != 200:
            logger.error(validate_case_response)
            raise Exception(
                f"Couldn't validate case on"
                f" mycase {validate_case_response}"
            )

        response = self.session.request("POST", url, data=payload)

        if response.status_code != 200:
            logger.error(response.text)
            raise Exception(f"Couldn't create case on mycase {response.text}")
