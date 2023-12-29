import logging

import requests
from rich.console import Console

console = Console()

logger = logging.getLogger(__name__)


class Endato(object):
    def __init__(self,url: str | None = None, key: str | None = None, secret: str | None = None) -> None:
        self.base_url = url or  "https://devapi.endato.com/PersonSearch"
        self.key = key or "4d73b426-77bd-4777-9edd-ea05a97a69ed"
        self.secret = secret or  "6021118d53a74d348c0d5b62d0b54135"
        self.headers = self.get_headers()

    def get_headers(self) -> dict:
        console.log("Beginning the process...")
        headers = {
            "Content-Type": "application/json",
            "galaxy-ap-name": self.key,
            "galaxy-ap-password": self.secret,
            "galaxy-search-type": "Person",
        }
        return headers

    def fetch(self, payload: dict) -> list:
        console.log(f"fetching with payload {payload}")
        response = requests.post(self.base_url, json=payload, headers=self.headers)
        if response.status_code != 200:
            console.log(f"fetching with response {response.status_code}")
            raise Exception(f"Error fetching data from API with status code {response.status_code}")
        response_data = response.json()
        list_of_persons = response_data.get("persons", [])
        console.log(f"find response of len  {len(list_of_persons)}")
        return list_of_persons

    def create_payload(self, first_name: str, last_name: str) -> dict:
        payload = {
            "FirstName": first_name,
            "MiddleName": "",
            "LastName": last_name,
            "Addresses": [
                {
                    "City": "",
                    "State": "",
                    "Zip": "",
                    "AddressLine1": "",
                    "AddressLine2": None,
                }
            ],
            "Dob": "",
            "Age": None,
            "AgeRange": "",
            "Phone": "",
            "Email": "",
            "Includes": ["Addresses", "PhoneNumbers"],
            "FilterOptions": ["IncludeLowQualityAddresses"],
            "Page": 1,
            "ResultsPerPage": 10,
        }
        return payload

    def paser_person(self, list_of_persons: list, age: int) -> dict:
        phone_numbers = [
            item["phoneNumber"]
            for person in list_of_persons
            if person.get("age") == 66
            for item in person.get("phoneNumbers", [])
        ]

        email_addresses = [
            item["emailAddress"]
            for person in list_of_persons
            if person.get("age") == 66
            for item in person.get("emailAddresses", [])
        ]

        return {"phone_numbers": phone_numbers, "email_addresses": email_addresses}


if __name__ == "__main__":
    endato = Endato()
    console.log(
        f"Beginning the process..{endato.base_url} {endato.key} {endato.secret} {endato.headers}"
    )
    payload = endato.create_payload("ALLAN", "HANAWAY")
    list_of_persons = endato.fetch(payload)
    console.log(f"find response of len  {len(list_of_persons)}")
    result = endato.paser_person(list_of_persons, 66)
    console.log(result)
