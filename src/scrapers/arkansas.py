import requests
import pandas as pd
from models.cases import Case
from models.leads import Lead
from src.scrapers.base import ScraperBase
from datetime import datetime
from tempfile import NamedTemporaryFile
from rich.console import Console
from rich.progress import Progress
import re
import os
from dotenv import load_dotenv
from twocaptcha import TwoCaptcha

TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')

console = Console()

class ArkansasScraper(ScraperBase):
    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)
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
        # Use regular expression to split on space, comma, hyphen, or period.
        # This can be expanded to include other delimiters if required.
        parts = re.split(r'[\s,\-\.]+', name)
        
        # Prepare variables for first, middle, and last names
        first_name = middle_name = last_name = ''

        # The list 'parts' now contains the split name parts.
        # How we assign these parts depends on the number of elements in 'parts'.
        if len(parts) > 2:
            first_name = parts[0]
            middle_name = ' '.join(parts[1:-1])  # All parts except first and last are considered middle names
            last_name = parts[-1]
        elif len(parts) == 2:
            first_name, last_name = parts
        elif len(parts) == 1:
            first_name = parts[0]

        return first_name, middle_name, last_name

    def get_cases(self, filing_date, page_number):
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
                    "paging" :{
                        "pageSize": 25,
                        "pageNumber": page_number
                    }
                },
                "caseType": "CITY DOCKET TRAFFIC",
                "docketDesc": "ALL"
            }
        }

        res = requests.post(
            url=url,
            json=data,
        )

        if res.status_code != 200:
            return [], 0
        
        total_pages = res.json().get('paging').get('totalPages')
        cases = res.json().get('items')

        return cases, total_pages
    
    def get_case_details(self, case_id):
        url = f"https://caseinfo.arcourts.gov/opad/api/cases/{case_id}"
        res = requests.get(url)

        if res.status_code != 200:
            return None
        
        charges = []
        offenses = res.json().get("caseOffenses")
        for offense in offenses:
            description = offense.get("offenseDesc")
            offense_date = offense.get("offenseViolationDate")
            age = offense.get("age")
            disp_date = offense.get("dispositionDate")
            charges.append({
                "description": description,
                "offense_date": offense_date,
                "age": age,
                "disp_date": disp_date
            })

        parties = [
            {
                "role": party.get("partyType"),
                "name": party.get("name")
            } 
            for party in res.json().get("caseParticipants")
        ]
        
        return charges, parties
    
    def scrape(self, search_parameters):
        filing_date = search_parameters["filing_date"]
        page_number = 1
        total_pages = None
        cases = []
        while page_number <= total_pages if total_pages is not None else True:
            case_data, total_pages = self.get_cases(filing_date, page_number)
            cases += case_data
            page_number += 1
        
        console.log(f"Total {len(cases)} cases")


        with Progress() as progress:
            task = progress.add_task("[red]Inserting cases...", total=len(cases))
            for case in cases:
                case_dict = {
                    value: case.get(key) for key, value in self.field_mapping.items()
                }
                case_id = case_dict["case_id"]
                charges, parties = self.get_case_details(case_id) # type: ignore
                
                offense_date = charges[0].get("offense_date") if charges else None
                offense_date = datetime.strptime(offense_date, "%Y-%m-%dT%H:%M:%S.%fZ") if offense_date else None
                
                filing_date = case_dict.get("filing_date")
                filing_date = datetime.strptime(filing_date, "%Y-%m-%dT%H:%M:%S.%fZ") if filing_date else None
                case_dict["filing_date"] = filing_date

                age = charges[0].get("age") if charges else None
                first_name, middle_name, last_name = self.split_full_name(parties[0].get("name"))
                case_dict = {
                    **case_dict,
                    "first_name": first_name,
                    "middle_name": middle_name,
                    "last_name": last_name,
                    "offense_date": offense_date,
                    "age": age,
                }

                print(case_dict)
                case = Case(**case_dict)
                lead = Lead(**case_dict)
                self.insert_case(case)
                self.insert_lead(lead)

                progress.advance(task, advance=1)