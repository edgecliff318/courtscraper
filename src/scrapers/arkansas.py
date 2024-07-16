""" Scraper for Arkansas Scraper"""
import asyncio
import re
import os
import requests
import pandas as pd

from dotenv import load_dotenv
from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile
from rich.console import Console
from rich.progress import Progress
from twocaptcha import TwoCaptcha

from models.cases import Case
from models.leads import Lead
from src.scrapers.base.scraper_base import ScraperBase

# Get API key from environment variables
TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')

console = Console()

# Define ArkansasScraper class inheriting from ScraperBase
class ArkansasScraper(ScraperBase):
    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)
    
    # Mapping of fields from the API to local fields
    field_mapping = {
        "caseId": "case_id",
        "caseDesc": "description",
        "caseFilingDate": "filing_date",
        "courtName": "court_id",
        "courtDesc": "court_desc",
        "courtLocation": "location",
        "caseType": "case_type",
        "statusDesc": "status",
    }

    def split_full_name(self, name):
        # Prepare variables for first, middle, and last names
        first_name = middle_name = last_name = ""

        # Use regular expression to split on space, comma, hyphen, or period.
        parts = re.split(r"[,]+", name)
        if len(parts) > 1:
            last_name = parts[0]

            # Remove the first space from the second part
            second_part = parts[1].lstrip()
            second_part = re.split(r"[\s]+", second_part)

            if len(second_part) > 1:
                first_name = second_part[0]
                middle_name = second_part[1]

            else:
                first_name = second_part[0]

        return first_name, middle_name, last_name

    def increase_date_by_one_day(self, date_str):
        """ Increase the given date string by one day. """
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        new_date_obj = date_obj + timedelta(days=1)
        return new_date_obj.strftime("%Y-%m-%d")

    def get_cases(self, filing_date, page_number):
        """ Fetch cases for a specific filing date and page number. """
        url = "https://caseinfo.arcourts.gov/opad/api/cases/search"
        data = {
            "caseSearchRequest": {
                "searchCriteria": {
                    "filterBy": [[
                        {
                            "fieldName": "caseFilingDate",
                            "operator": "GREATER_THAN",
                            "fieldValue": f"{filing_date}T00:00:00.000Z"
                        },
                        {
                            "fieldName": "caseFilingDate",
                            "operator": "LESS_THAN",
                            "fieldValue": f"{filing_date}T23:59:59.000Z"
                        }
                    ]],
                    "paging": {
                        "pageSize": 25,
                        "pageNumber": page_number
                    }
                },
                "caseType": "CITY DOCKET TRAFFIC",
                "docketDesc": "ALL"
            }
        }

        try:
            res = requests.post(url=url, json=data)
            res.raise_for_status()  # Raises an error for bad responses (4XX and 5XX)
        except requests.RequestException as e:
            console.log(f"Failed to retrieve cases for date {filing_date}: {e}")
            return [], 0

        response_data = res.json()
        total_pages = response_data.get('paging', {}).get('totalPages', 0)
        cases = response_data.get('items', [])

        return cases, total_pages

    def get_court_id(self, case_dict):
        """ Generate or fetch court information based on case data. """
        self.courts = {}
        court_code = f"AR_{case_dict.get('court_id').upper()}"
        county_name = case_dict.get('court_id')
        county_code = case_dict.get('court_id')
        if court_code not in self.courts:
            self.courts[court_code] = {
                "code": court_code,
                "county_code": county_code,
                "enabled": True,
                "name": f"Arkansas, {county_name}",
                "state": "AR",
                "type": "CT",
            }
            self.insert_court(self.courts[court_code])

        return court_code       

    def get_case_details(self, case_id):
        """ Fetch detailed information for a specific case ID. """
        url = f"https://caseinfo.arcourts.gov/opad/api/cases/{case_id}"
        try:
            res = requests.get(url)
            res.raise_for_status()
        except requests.RequestException as e:
            console.log(f"Failed to retrieve details for case {case_id}: {e}")
            return None, []

        response_data = res.json()
        # Extract charges
        charges = [{
            "description": offense.get("offenseDesc"),
            "offense_date": offense.get("offenseViolationDate"),
            "age": offense.get("age"),
            "disp_date": offense.get("dispositionDate")
        } for offense in response_data.get("caseOffenses", [])]

        # Extract parties
        parties = [{
            "role": party.get("partyType"),
            "name": party.get("name")
        } for party in response_data.get("caseParticipants", [])]

        return charges, parties 

    def scrape_cases_for_filing_date(self, filing_date):
        """ Scrape all case data for a specific filing date. """
        page_number = 1
        total_pages = None
        cases = []

        while total_pages is None or page_number <= total_pages:
            case_data, total_pages = self.get_cases(filing_date, page_number)
            cases.extend(case_data)
            page_number += 1
        
        return cases if cases else None
    
    def process_cases(self, cases):
        """ Process raw case data into structured case dictionaries. """
        case_dicts = []

        for case in cases:
            case_dict = {value: case.get(key) for key, value in self.field_mapping.items()}
            case_id = case_dict["case_id"]

            case_dict["court_id"] = self.get_court_id(case_dict)
            charges, parties = self.get_case_details(case_id)

            if charges:
                offense_date = charges[0].get("offense_date")
                if offense_date:
                    offense_date = datetime.strptime(offense_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                case_dict["offense_date"] = offense_date
                case_dict["age"] = charges[0].get("age")

            filing_date = case_dict.get("filing_date")
            if filing_date:
                filing_date = datetime.strptime(filing_date, "%Y-%m-%dT%H:%M:%S.%fZ")
            case_dict["filing_date"] = filing_date
            case_dict["case_date"] = filing_date

            if parties:
                first_name, middle_name, last_name = self.split_full_name(parties[0].get("name"))
                case_dict.update({
                    "first_name": first_name,
                    "middle_name": middle_name,
                    "last_name": last_name,
                })

            status = case_dict.get("status")
            if status:
                case_dict["status"] = "new"

            case_dict.update({
                "charges": charges,
                "parties": parties,
                "court_code": case_dict.get("court_id"),
                "state": "AR",
                "source": "arkansas_state",
            })
            case_dicts.append(case_dict)
        return case_dicts
    
    def scrape(self):
        """ Main scraping function to handle the entire scraping process. """
        last_filing_date = self.state.get("last_filing_date", "2024-05-01")
        filing_date = last_filing_date
        not_found_count = 0
        while True:
            try:
                cases = []
                if not_found_count > 10:
                    console.log("Too many filing dates not found. Ending the search.")
                    break

                filing_date = self.increase_date_by_one_day(filing_date)
                case_data = self.scrape_cases_for_filing_date(filing_date)

                if case_data is None:
                    console.log(
                        f"Case {case_data} not found. Skipping ..."
                    )
                    not_found_count += 1
                    continue

                not_found_count = 0
                console.log(
                    f"Downloading case details for {last_filing_date}"
                )
                cases.extend(case_data)
                          
                console.log(f"Total {len(cases)} cases")

                case_dicts = self.process_cases(cases)        
                for case_dict in case_dicts:
                    case_id = case_dict["case_id"]
                    if self.check_if_exists(case_id):
                        console.log(
                            f"Case {case_id} already exists. Skipping..."
                        )
                        continue

                    console.log(f"Inserting case {case_id}...")
                    self.insert_case(case_dict)
                    console.log(
                        f"Inserted case for {case_id})"
                    )
                    self.insert_lead(case_dict)
                    console.log(
                        f"Inserted lead for {case_id}"
                    )
                
                self.state["last_filing_date"] = filing_date
                # self.update_state()
            except Exception as e:
                console.log(f"Failed to insert case - {e}")
                continue

    
if __name__ == "__main__":
    arkansasscraper = ArkansasScraper()
    asyncio.run(arkansasscraper.scrape())
    console.log("Done running", __file__, ".")