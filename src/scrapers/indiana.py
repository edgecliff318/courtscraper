import requests
import os
import pandas as pd
import re
import time
from datetime import datetime
from tempfile import NamedTemporaryFile
from rich.console import Console
from rich.progress import Progress
from models.cases import Case
from models.leads import Lead
from src.scrapers.base.scraper_base import ScraperBase

from twocaptcha import TwoCaptcha

TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')
print(TWOCAPTCHA_API_KEY)
console = Console()

class IndianaScraper(ScraperBase):
    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)
    field_mapping = {
        "CaseNumber": "case_id",
        "Court": "court_desc",
        "CaseType": "case_type",
        "CaseStatus": "case_status",
        "FileDate":"filing_date",
        "AppearByDate": "court_date",
        "Style": "description",
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
    
    def get_case_detail(self, case_token):
        url = "https://public.courts.in.gov/mycase/Case/CaseSummary"
        params = {
            'SRCT': '',
            'CaseToken': case_token,
            '_': '1713862566949'
        }
        headers = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            return None
    
    def extract_case_info(self, case_detail):
        case_dict = {
            value: case_detail.get(key) for key, value in self.field_mapping.items()
        }
        case_dict["filing_date"] = datetime.strptime(case_dict["filing_date"], "%m/%d/%Y") if case_dict["filing_date"] else None
        case_dict["court_date"] = datetime.strptime(case_dict["court_date"], "%m/%d/%Y") if case_dict["court_date"] else None
        
        court_id = case_detail.get("CountyCode")+case_detail.get("CourtCode")
        case_id = case_detail.get("case_id")
        if case_id == None:
            case_id = "None"
        else:
            case_id = case_id.astype(str)
        charges = [
            {
                "offense_date": charge.get("OffenseDate"),
                "description": charge.get("OffenseDescription"),
                "degree": charge.get("OffenseDegree"),
            }
            for charge in case_detail.get("Charges", [])
        ]
        if charges:
            offense_date = charges[0].get("offense_date")
            offense_date = datetime.strptime(offense_date, "%m/%d/%Y") if offense_date else None
        else:
            offense_date = None

        events = [
            {
                "event_date": event.get("EventDate"),
                "event_description": event.get("Description"),
                "event_type": event.get("EventType"),
                "judge": event.get("Judge"),
                "comment": event.get("CaseEvent").get("Comment") if event.get("CaseEvent") else None
            }
            for event in case_detail.get("Events", [])
        ]
        parties = [
            {
                "role": party.get("ExtConnCodeDesc"),
                "name": party.get("Name"),
            }
            for party in case_detail.get("Parties", [])
        ]
        defendant = [party for party in case_detail.get("Parties") if party.get("ExtConnCode") == "DEF"]
        if len(defendant) == 0:
            return {
                "court_id": court_id,
                "case_id": case_id,
                "charges": charges,
                "offense_date": offense_date,
                "events": events,
                "parties": parties,
                **case_dict,
            }
        else:
            defendant = defendant[0]
        first_name, middle_name, last_name = self.split_full_name(defendant.get("Name"))
        birth_date = defendant.get("DOB")
        address_line_1 = defendant.get("Address").get("Line1") if defendant.get("Address") else None
        address_city = defendant.get("Address").get("City") if defendant.get("Address") else None
        address_state_code = defendant.get("Address").get("State") if defendant.get("Address") else None
        address_zip = defendant.get("Address").get("Zip") if defendant.get("Address") else None

        return {
            "court_id": court_id,
            "charges": charges,
            "offense_date": offense_date,
            "events": events,
            "parties": parties,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "birth_date": birth_date,
            "address_line_1": address_line_1,
            "address_city": address_city,
            "address_state_code": address_state_code,
            "address_zip": address_zip,
            **case_dict,
        }
    
    def get_cases(self, filed_date, captcha=None):
        url = "https://public.courts.in.gov/mycase/Search/SearchCases"
        captcha_answer = {"Key":captcha.get("key"),"Answer":captcha.get("answer"),"Refresh":False} if captcha else None
        data = {
            "Mode": "ByCase", 
            "Categories": ["CR"],
            "CaptchaAnswer": captcha_answer,
            "Advanced": True,
            "ActiveFlag": "Open",
            "FileStart": filed_date,
            "FileEnd": filed_date,
            "Skip": 0,
            "Take": 9999,
            "Sort": "FileDate DESC"
        }
        headers = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        res = requests.post(url, json=data, headers=headers)
        
        if res.status_code != 200:
            return []
        elif res.json().get("Results") is None:
            img = res.json().get('Url')
            key = res.json().get('CaptchaKey')
            answer = self.solver.normal(img)["code"]
            return self.get_cases(filed_date, {"key":key,"answer":answer})
        else:
            return [case.get("CaseToken") for case in res.json().get("Results")]
    
    def scrape(self, search_parameters):
        filed_date = search_parameters['filed_date']
        case_tokens = self.get_cases(filed_date)
        console.log(f"Found {len(case_tokens)} cases")
        with Progress() as progress:
            task = progress.add_task("[red]Inserting cases...", total=len(case_tokens))
            for case_token in case_tokens:
                case_detail = self.get_case_detail(case_token)
                if case_detail:
                    case_dict = self.extract_case_info(case_detail)
                    self.insert_case(case_dict)
                    self.insert_lead(case_dict)
                else:
                    console.log(case_token)
                time.sleep(10)  # Add additional sleep time to avoid get blocked
                progress.update(task, advance=1)