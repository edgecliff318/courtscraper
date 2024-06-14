from playwright.async_api import async_playwright, TimeoutError
import requests
import re
import os
import pandas as pd
from urllib.parse import urlparse, parse_qs
from datetime import date, datetime, time
from tempfile import NamedTemporaryFile
from rich.console import Console
from rich.progress import Progress
from models.cases import Case
from models.leads import Lead
from src.scrapers.base.scraper_base import ScraperBase

from twocaptcha import TwoCaptcha

TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')

console = Console()

class DistrictCourtScraper(ScraperBase):
    field_mapping = {
        "CaseNumber": "case_id",
        "Name": "name",
        "Address": "address_line_1",
        "Court": "court_id",
        "Charges": "charges",
        "FiledDate":"filing_date",
        "Status": "status",
        "Locality": "location",
        "DOB":"birth_date"
    }
    
    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)
    
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
    
    async def init_browser(self):
        console.log("Initation of Browser...")
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(headless=False)
        context = await self.browser.new_context()
        self.page = await context.new_page()
        self.url = "https://eapps.courts.state.va.us/gdcourts/landing.do"
        await self.page.goto(self.url)

        await self.page.wait_for_timeout(2000)
        accept_button = await self.page.query_selector('input.submitBox')
        if accept_button:
            await accept_button.click()
        else:
            print("The 'Accept' button was not found.")
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(2000)

    async def get_courts(self):
        console.log("Getting courts...")
        court_names = await self.page.query_selector_all("input[name='courtName']")
        court_ids = await self.page.query_selector_all("input[name='courtFips']")

        courts = []
        for court_id, court_name in zip(court_ids, court_names):
            court = {
                "court_id": await court_id.get_attribute("value"),
                "court_desc": await court_name.get_attribute("value")
            }
            courts.append(court)

        return courts

    async def search_case_number(self, case_number, court_id):
        url = f"https://eapps.courts.state.va.us/gdcourts/criminalCivilCaseSearch.do?fromSidebar=true&formAction=searchLanding&searchDivision=T&searchFipsCode={court_id}&curentFipsCode={court_id}"
        await self.page.goto(url)
        search_case_element = await self.page.query_selector("#displayCaseNumber")
        await search_case_element.fill(f"{case_number}") # type:ignore
        
        submit_button = await self.page.query_selector('input.submitBox')
        if submit_button:
            await submit_button.click()
        else:
            print("The 'btnSearch' button was not found.")
        await self.page.wait_for_load_state("networkidle")
    
    async def extract_info(self):
        case_row = await self.page.query_selector("#toggleCase")
        table = await case_row.query_selector("table") # type:ignore
        tds = await table.query_selector_all("td") # type:ignore
        eliminate_key = [':','\n','\t','\xa0']
        
        case_row_dict = {}
        for i in range(0, len(tds), 2):
            key = await tds[i].text_content()
            value = await tds[i + 1].text_content()
            for element in eliminate_key:
                key = key.replace(element, "") # type:ignore
                key = key.strip()
                value = value.replace(element, "") # type:ignore
                value = value.strip()
            
            case_row_dict[key] = value
                
        charge_row = await self.page.query_selector("#toggleCharge")
        table = await charge_row.query_selector("table") # type:ignore
        tds = await table.query_selector_all("td") # type:ignore
        
        charge_row_dict = {}
        for i in range(0, len(tds), 2):
            key = await tds[i].text_content()
            key = key.replace(":","").strip() if key else None
            value = await tds[i + 1].text_content()
            value = value.replace(":","").strip() if value else None
            charge_row_dict[key] = value
        
        charges = []
        charge = {}
        for key, value in charge_row_dict.items():
            for element in eliminate_key:
                key = key.replace(element, "")
                key = key.strip().lower()
            if key == "charge" :
                charge["description"] = value
            elif key == "offensedate":
                charge["offense_date"] = value
        charges.append(charge)

        return {
            **case_row_dict,
            "charges": charges
        }
    
    async def scrape(self, search_parameters):
        case_number = search_parameters['case_number']
        
        await self.init_browser()
        courts = await self.get_courts()

        court_id = courts[0]['court_id']
        court_desc = courts[0]['court_desc']
        
        await self.search_case_number(case_number, court_id)
        
        case_dict = await self.extract_info()
        case_dict = {
            value: case_dict.get(key) for key, value in self.field_mapping.items()
        }
        first_name, middle_name, last_name = self.split_full_name(case_dict.get("name"))

        case_dict = {
            **case_dict,
            "court_id": court_id,
            "court_desc": court_desc,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
        }
        print(case_dict)
        with Progress() as progress:
            task = progress.add_task(
                "[red]Inserting cases...", total=len(case_dict)
            )
            
            case_id = case_dict.get("case_id")
            if self.check_if_exists(case_id):
                console.log(
                    f"Case {case_id} already exists. Skipping..."
                )
                progress.update(task, advance=1)
            else:
                self.insert_case(case_dict)
                self.insert_lead(case_dict)

        await self.browser.close()