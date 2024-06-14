import requests
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError
from urllib.parse import urlparse, parse_qs
from datetime import date, datetime, time
from tempfile import NamedTemporaryFile
from rich.console import Console
from rich.progress import Progress

from models.cases import Case
from models.leads import Lead
from src.scrapers.base.scraper_base import ScraperBase

import os
from twocaptcha import TwoCaptcha
TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')

console = Console()
class NorthCarolinaScraper(ScraperBase):
    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)

    async def init_browser(self):
        console.log("Initation of Browser...")
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(headless=False)
        context = await self.browser.new_context()
        self.page = await context.new_page()
        await self.page.goto(self.url)
    
    async def search_by_case_number(self, case_number, county_number):
        console.log("Submitting Search Query...")
        search_input_element = await self.page.query_selector("#caseCriteria_SearchCriteria")
        await search_input_element.fill(f"{case_number}-{county_number}")

        recaptcha_element = await self.page.query_selector('div.g-recaptcha')
        if recaptcha_element:
            site_key = await recaptcha_element.get_attribute('data-sitekey')
            response = self.solver.recaptcha(
                sitekey=site_key,
                url=self.url
            )
            code = response['code']
            response_textarea = await recaptcha_element.query_selector('textarea#g-recaptcha-response')
            if response_textarea:
                await response_textarea.evaluate('el => el.value = "{}"'.format(code))
            else:
                print("The 'g-recaptcha-response' textarea was not found.")

        submit_button = await self.page.query_selector('input#btnSSSubmit')
        if submit_button:
            await submit_button.click()
        else:
            print("The 'btnSearch' button was not found.")
        
        await self.page.wait_for_selector("#CasesGrid", state="attached", timeout=10000)
        
        caselinks = await self.page.query_selector_all("a.caseLink")
        case_keys = [await caselink.get_attribute("data-url") for caselink in caselinks]
        case_keys = [parse_qs(urlparse(case_keys).query).get('id', [None])[0] for case_keys in case_keys]

        return case_keys

    def get_basic_info(self, key):
        res = requests.get(
            url="https://portal-nc.tylertech.cloud/app/RegisterOfActionsService/CaseSummariesSlim",
            params={
                "key": key
            }
        )
        case_detail = res.json().get("CaseSummaryHeader")
        case_id = case_detail.get("CaseNumber")
        court_id = str(case_detail.get("NodeId"))
        filed_date = datetime.strptime(case_detail.get("FiledOn"), "%m/%d/%Y")if case_detail.get("FiledOn") else None
        court_date = datetime.strptime( case_detail.get("AppearBy"), "%m/%d/%Y") if case_detail.get("AppearBy") else None
        court_desc = case_detail.get("NodeName")
        description = case_detail.get("Style")
        judge = case_detail.get("Judge")

        return {
            "case_id": case_id,
            "court_id": court_id,
            "filing_date": filed_date,
            "court_date": court_date,
            "court_desc": court_desc,
            "description": description,
            "judge": judge
        }

    def get_charges_info(self, key):
        res = requests.get(
            url=f"https://portal-nc.tylertech.cloud/app/RegisterOfActionsService/Charges('{key}')",
            params={
                "mode": "portalembed"
            }
        )
        
        if res.status_code != 200:
            return {}
        charges_info = res.json().get("Charges")
        if len(charges_info) == 0:
            return {}
        
        offense_date = datetime.strptime( charges_info[0].get("OffenseDate"), "%m/%d/%Y") if charges_info[0].get("OffenseDate") else None
        charges = [
            {
                "charge_desc": charge.get("ChargeOffense").get("ChargeOffenseDescription"),
                "degree": charge.get("ChargeOffense").get("Degree"),
                "fine": charge.get("ChargeOffense").get("FineAmount"),
                "statute": charge.get("ChargeOffense").get("Statute"),
            }
            for charge in charges_info
        ]

        return {
            "charges": charges, 
            "offense_date": offense_date
        }
    
    def get_parties_info(self, key):
        res = requests.get(
            url=f"https://portal-nc.tylertech.cloud/app/RegisterOfActionsService/Parties('{key}')",
            params={
                "mode": "portalembed",
                "$top": 50,
                "$skip": 0
            }   
        )

        if res.status_code != 200:
            return {}
        parties = res.json().get("Parties")
        if len(parties) == 0:
            return {}
        
        participants = [
            {
                "role": party.get("ConnectionType"),
                "name": party.get("FormattedName"),
            }
            for party in parties
        ]
        defendant = [party for party in parties if party.get("ConnectionType") == "Defendant"][0]

        return {
            "participants": participants,
            "first_name": defendant.get("NameFirst"),
            "last_name": defendant.get("NameLast"),
            "middle_name": defendant.get("NameMid"),
            "gender": defendant.get("Gender"),
            "birth_date": defendant.get("DateofBirth"),
            "address_line_1": defendant.get("Addresses")[0].get("AddressLine1"),
            "address_city": defendant.get("Addresses")[0].get("City"),
            "address_zip": defendant.get("Addresses")[0].get("PostalCode"),
            "address_state_code": defendant.get("Addresses")[0].get("State"),
        }
    
    async def scrape(self, search_parameters):
        case_number = search_parameters.get("case_number")
        county_number = search_parameters.get("county_number")
        
        self.url = "https://portal-nc.tylertech.cloud/Portal/Home/Dashboard/29"
        await self.init_browser()
        case_keys = await self.search_by_case_number(case_number, county_number)

        console.log("Extracting Case Information...")
        
        for key in case_keys:
            basic_info = self.get_basic_info(key)
            charges_info = self.get_charges_info(key)
            parties_info = self.get_parties_info(key)
            
            case_dict = {
                **basic_info,
                **charges_info,
                **parties_info
            }
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