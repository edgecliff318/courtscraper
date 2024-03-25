import datetime
import json
import logging
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from src.components import conversation
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
        payload = "utf8=%E2%9C%93&login_session%5Bemail%5D=team%40tickettakedown.com&login_session%5Bpassword%5D=TTDpro24!"
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
            contacts = self.get_similar_contacts(
                lead.first_name, lead.last_name
            )
            for contact in contacts:
                if contact.get("email") == lead.email:
                    return contact.get("id")

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

        first_name = (
            lead.first_name.capitalize() if lead.first_name is not None else ""
        )
        middle_name = (
            f"{lead.middle_name.capitalize()[:1]}."
            if lead.middle_name is not None and len(lead.middle_name) > 0
            else ""
        )
        last_name = (
            lead.last_name.capitalize() if lead.last_name is not None else ""
        )

        payload_dict = {
            "has_new_company": False,
            "has_existing_company": False,
            "court_case": {
                "name": (
                    f"TTD23 {first_name} {middle_name}"
                    f" {last_name}  - {case.location}"
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
                        "value": (
                            "CIRCUIT"
                            if (
                                case.court_type is not None
                                and (
                                    "circ" in case.court_type.lower()
                                    or case.court_type.lower() == "c"
                                )
                            )
                            else "MUNICIPAL"
                        ),
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
                        "value": (
                            case.judge.get("formatted_name")
                            if case.judge is not None
                            else ""
                        ),
                        "custom_field_id": "552502",
                    },
                    "6": {
                        "value": charges,
                        "custom_field_id": "561060",
                    },
                    "7": {"value": "", "custom_field_id": "561063"},
                    "8": {"value": "", "custom_field_id": "561643"},
                    "9": {
                        "value": (
                            case.fine.get("total_amount", "")
                            if case.fine is not None
                            else ""
                        ),
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

    def get_similar_contacts(self, first_name, last_name):
        url = "https://meyer-attorney-services.mycase.com/users/similar.json"
        params = {
            "first_name": first_name,
            "last_name": last_name,
            "type": "Client",
        }
        response = self.session.request("GET", url, params=params)
        return response.json().get("similar_users", [])

    def search_contacts(self, query):
        # https://meyer-attorney-services.mycase.com/search?search_term=ayoub.ennassiri%40neoinvest.ai&search_filter=%5B%22all%22%5D

        url = "https://meyer-attorney-services.mycase.com/search"
        params = {
            "search_term": query,
            "search_filter": '["all"]',
        }

        response = self.session.request("POST", url, params=params)

        return response.json()

    def search_case(self, case_id):
        url = f"https://meyer-attorney-services.mycase.com/search/auto_complete.json?term={case_id}&filter_type=cases"

        response = self.session.request("GET", url)

        """
        [
            {
                "record_type": "court_case",
                "record_id": 31946235,
                "label": "TTD23 Abby M. Ross  - Carthage Municipal - 190203419",
                "category": "Cases",
                "archived": false
            }
        ]
        """

        for case in response.json():
            record_id = case.get("record_id")
            label = case.get("label")

            if case_id in label:
                break

        url = f"https://meyer-attorney-services.mycase.com/court_cases/{record_id}/case_contacts_data.json"

        response = self.session.request("GET", url)

        return {
            "clients": response.json().get("clients", []),
            "staff": response.json().get("staff", []),
            "record_id": record_id,
        }

    def reload_sharing(self, mycase_case_id):
        url = "https://meyer-attorney-services.mycase.com/appointments/reload_sharing.json"

        payload = json.dumps(
            {"case_id": mycase_case_id, "no_case_link": False}
        )

        response = self.session.request("POST", url, data=payload)

        return response.json()

    def get_contact(self, first_name, last_name, email):
        contacts = self.get_similar_contacts(first_name, last_name)
        for contact in contacts:
            if contact.get("email") == email:
                return contact.get("id")
        return None

    def add_event(self, case_details, reminders=None):
        court_date = ""
        court_time = ""
        court_address = ""

        if case_details.mycase_case_id is None:
            raise Exception("Case is not uploaded to MyCase")

        mycase_case_id = case_details.mycase_case_id

        sharing_rules = self.reload_sharing(case_details.get("id"))

        url = (
            "https://meyer-attorney-services.mycase.com/appointment_rules.json"
        )

        payload = json.dumps(
            {
                "appointment_rule": {
                    "item_category_id": None,
                    "court_case_id": mycase_case_id,
                    "name": "EVENT_NAME",
                    "start_date": "03/09/2024",
                    "start_time": "06:00 PM",
                    "end_date": "03/09/2024",
                    "end_time": "07:00 PM",
                    "location_id": None,
                    "description": "DESCRIPTION",
                    "private": False,
                },
                "google_sync": False,
                "new_record": True,
                "creating_new_location": True,
                "location": {
                    "name": "LOCATION_NAME",
                    "reusable": False,
                    "address_attributes": {
                        "street": "LOCATION_ADDRESS",
                        "street2": "LOCATION_ADDRESS_2",
                        "city": "CITY",
                        "state": "MO",
                        "zip_code": "ZIP",
                        "country": "US",
                    },
                },
                "appointment_id": None,
                "sharing": [27310503, 27081302, 27294644],
                "attendance": [],
                "format_workflow_application": False,
                "reminders": [
                    {
                        "user_type": "client",
                        "type": "text",
                        "number": "1",
                        "duration": "week",
                    },
                    {
                        "user_type": "client",
                        "type": "client",
                        "number": "4",
                        "duration": "week",
                    },
                    {
                        "user_type": "client",
                        "type": "text",
                        "number": "1",
                        "duration": "day",
                    },
                ],
                "non_linked_sharing": {"shared": [], "required": []},
            }
        )

        response = self.session.request("POST", url, data=payload)
        return response.json()

    def get_cases(self, client_id):
        url = "https://meyer-attorney-services.mycase.com/autocomplete/cases.json"
        params = {"term": "", "scoped_by_user_id": client_id}
        response = self.session.request("GET", url, params=params)

        """
        output = [
            {
                "id": 31946235,
                "name": "TTD23 Abby M. Ross  - Carthage Municipal - 190203419"
            }
        ]
        """
        return response.json()

    def get_converation(self, mycase_case_id):
        # https://meyer-attorney-services.mycase.com/text_messages.json?search_term=&court_case_id=31946235&include_unjoined=true&include_archived=true&unread_only=false&page_number=1
        url = "https://meyer-attorney-services.mycase.com/text_messages.json"
        params = {
            "search_term": "",
            "court_case_id": mycase_case_id,
            "include_unjoined": True,
            "include_archived": True,
            "unread_only": False,
            "page_number": 1,
        }
        response = self.session.request("GET", url, params=params)
        """
        {
            "conversations": [
                {
                    "id": 831383,
                    "client": {
                        "id": 27294644,
                        "display_name": "Abby Ross (Client)",
                        "initials": "",
                        "avatar_url": null,
                        "type": "Client"
                    },
                    "external_phone_number": "+18165188838",
                    "archived_at": null,
                    "archived_by": null,
                    "last_text_message": {
                        "id": 37480397,
                        "body": "What's up ?",
                        "timestamp": "2024-03-17T16:56:36-05:00"
                    },
                    "unread_count": 0,
                    "mute_for_current_user": false,
                    "joined_for_current_user": true
                }
            ],
            "has_more": false
        }
        """
        conversations = response.json().get("conversations", [])
        conversation_id = conversations[0].get("id")
        return conversation_id

    def get_text_messages(self, conversation_id):
        # https://meyer-attorney-services.mycase.com/text_messages/831383/messages.json
        url = f"https://meyer-attorney-services.mycase.com/text_messages/{conversation_id}/messages.json"

        response = self.session.request("GET", url)
        """
        {
        "messages": [
            {
                "id": 8499680,
                "type": "outgoing",
                "body": "Hi Shawn, this is a test text message. Let me know if you receive this and reply back.",
                "sent_by": {
                    "id": 27310503,
                    "display_name": "Sam Mahmud (Attorney)",
                    "initials": "SM",
                    "avatar_url": "https://s3.amazonaws.com/com.mycase.prod3-main/sharded/user_avatar/b3fa2f4c-c25c-4da4-be2a-b8229af974f3/small_sam_ttd.jpeg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIA3V65YTC5BSAW6VXY%2F20240317%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240317T214244Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEL3%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJIMEYCIQDWNmchMeIl3LzW4yjKcsCeV7oPGbR8ECjlUWfKd50cTgIhAKwlH0chiWwbjKjVYFZF0cJuOM3DMhS9wqYNv3c5v2BZKsUCCMb%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEQABoMODAzMDg3MDk1OTk0IgyF9IFTSX%2BvpSkfY%2BgqmQIc9ocJ1jawKIvwR7lNF9U4%2BGBSC4tjhKEZXiFaQv6WFBdiqWKUiimjGnn%2FQKxAU0lzEpXjM%2FTHjOaHTj1p2J0oBxy2IkYjJIVNnuz6ASSYPNXpHK1kXoJSD%2FYLKUDMmrtqPZyPBPluNPM7lUCaIU0gyd6igracbQTiMAHX13R2P9%2FJBMOyEG%2FdbmlCuO2xuKi4sSniZv2zz2owuTaAHJCL1S00i0RjFLJOIu63S4xJkUNOUDhEjxGLpHMVqaBTAFiCtbA0yVjDKpmA03fOoyOZEFFPq5ojIp76C8pDK9ynU0hqwrb%2FMakL3sHrZkhokIQxSuW0bq0dyb1zzR3wE45xgFfpqrFwH7rOoMDqaqYG2qTErmP8YrT3UjD6qt2vBjqcAXiSuFEwiNVbSN5COnWQi9SVxq6mq%2Bafv0Wjz0D90hmWpVZvcim0isOl%2BggvMOnvgNVmj64Gbu74MPdtP2yCCooarV07aDXuF71SxRlag1mHQ%2FU8VdMuQMcOy2ep%2B7RgP7172wqjCd3FFAX16uLA4k%2BtetjOq9YmomgkidWp%2BlTuPXhhgYqSMH%2Fz988Qw5%2BgCSyzeuAdKk2lrNiuKA%3D%3D&X-Amz-SignedHeaders=host&X-Amz-Signature=102b2b0c2f0ba8c5155aadd74236a2849022d12e74abd3a7225269f770ae6b40",
                    "type": "Lawyer"
                },
                "timestamp": "2021-12-30T11:21:29-06:00",
                "status": "delivered",
                "error_message": null,
                "has_media": null,
                "mms_attachments": null
            },
            {
                "id": 8499687,
                "type": "incoming",
                "body": "Hello ",
                "sent_by": {
                    "id": 27294644,
                    "display_name": "Abby Ross (Client)",
                    "initials": "AR",
                    "avatar_url": null,
                    "type": "Client"
                },
                "timestamp": "2021-12-30T11:21:43-06:00",
                "status": "received",
                "error_message": null,
                "has_media": null,
                "mms_attachments": null
            },
            {
                "id": 37480397,
                "type": "outgoing",
                "body": "What's up ?",
                "sent_by": {
                    "id": 45937206,
                    "display_name": "Team Ticket Takedown (Staff)",
                    "initials": "TT",
                    "avatar_url": null,
                    "type": "Lawyer"
                },
                "timestamp": "2024-03-17T16:56:36-05:00",
                "status": "delivered",
                "error_message": null,
                "has_media": null,
                "mms_attachments": null
            }
        ]
        }
        """
        messages = response.json().get("messages", [])
        return messages

    def create_text_message(self, mycase_case_id, message):
        conversation_id = self.get_converation(mycase_case_id)
        url = f"https://meyer-attorney-services.mycase.com/text_messages/{conversation_id}/send_message.json"

        payload = json.dumps(
            {"message_body": message, "court_case_id": mycase_case_id}
        )

        response = self.session.request("POST", url, data=payload)
        """
        {
            "text_message": {
                "id": 37480531,
                "type": "outgoing",
                "body": "MESSAGE TEST",
                "sent_by": {
                    "id": 45937206,
                    "display_name": "Team Ticket Takedown (Staff)",
                    "initials": "TT",
                    "avatar_url": null,
                    "type": "Lawyer"
                },
                "timestamp": "2024-03-17T17:23:49-05:00",
                "status": "accepted",
                "error_message": null,
                "has_media": null,
                "mms_attachments": null
            },
            "time_trackable_item_id": 159114488
        }
        """
        return response.json()

    def create_mycase_message(
        self,
        mycase_case_id,
        client_id,
        subject,
        message,
        attachments,
        case_name,
    ):
        current_timestamp = int(datetime.datetime.now().timestamp() * 1000)
        url = f"https://meyer-attorney-services.mycase.com/messages/new?court_case={mycase_case_id}&_={current_timestamp}"

        response = self.session.request("GET", url)

        # Get the following data-id
        # <form class="calico_lightbox" id="message_form" data-id="21431553" action="/messages/21431553" accept-charset="UTF-8"
        # <input name="utf8" type="hidden" value="&#x2713;" autocomplete="off" /><input type="hidden" name="_method" value="patch" autocomplete="off" /><input type="hidden" name="authenticity_token" value="ESUbP5xswZCAkRVMFi5jWgtymBYk6a52jO11azNSWGwI8-oHh51GljHUc53ooOPdrAx3lHfDsoLg9Zc7gsFvyA" autocomplete="off" />
        soup = BeautifulSoup(response.text, "html.parser")
        message_form = soup.find("form", {"id": "message_form"})
        message_id = message_form.get("data-id")
        authenticity_token = message_form.find(
            "input", {"name": "authenticity_token"}
        ).get("value")

        # Prepare the form data
        form_data = {
            "utf8": "✓",
            "_method": "patch",
            "authenticity_token": authenticity_token,
            "message[court_case_id]": mycase_case_id,
            "adding_time_entry": "false",
            "to_user": "",
            "to_selected_id": f"client_{client_id}",
            "message[global_clients]": "0",
            "message[global_lawyers]": "0",
            "to[]": f"{client_id}",
            "message[private_reply]": "false",
            "courtcase_search_name": case_name,
            "message[subject]": subject,
            "message[initial_message]": message,
        }
        form_data = urlencode(form_data)

        # Update the headers to include the content type
        self.session.headers.update(
            {
                "content-type": "application/x-www-form-urlencoded",
            }
        )

        # Post the message
        message_url = (
            f"https://meyer-attorney-services.mycase.com/messages/{message_id}"
        )

        response = self.session.request("POST", message_url, data=form_data)

        # Send the message
        message_send_url = f"https://meyer-attorney-services.mycase.com/messages/{message_id}/send_message"
        response = self.session.request(
            "POST", message_send_url, data=form_data
        )
        return response.json()
