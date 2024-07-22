""" Scraper for North Carolina Court """
import asyncio
import requests
import os
import pandas as pd

from playwright.async_api import async_playwright, TimeoutError
from urllib.parse import urlparse, parse_qs
from datetime import date, datetime, time
from tempfile import NamedTemporaryFile
from rich.console import Console

from models.cases import Case
from models.leads import Lead
from src.scrapers.base.scraper_base import ScraperBase

from twocaptcha import TwoCaptcha

TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')

console = Console()

class NorthCarolinaScraper(ScraperBase):
    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)

    async def init_browser(self):
        console.log("Initation of Browser...")
        pw = await async_playwright().start()
        # Proxy 9090
        self.browser = await pw.chromium.launch(
            headless=True,
            # args=["--proxy-server=socks5://localhost:9090"]
        )

        context = await self.browser.new_context()
        self.page = await context.new_page()
        await self.page.goto(self.url)
    
    async def search_by_case_number(self, case_number):
        await self.page.goto(self.url)
        console.log("Submitting Search Query...")
        search_input_element = await self.page.query_selector("#caseCriteria_SearchCriteria")
        await search_input_element.fill(f"{case_number}-500")

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
            "sex": defendant.get("Gender"),
            "race": defendant.get("Race"),
            "birth_date": defendant.get("DateofBirth"),
            "address_line_1": defendant.get("Addresses")[0].get("AddressLine1"),
            "address_city": defendant.get("Addresses")[0].get("City"),
            "address_zip": defendant.get("Addresses")[0].get("PostalCode"),
            "address_state_code": defendant.get("Addresses")[0].get("State"),
        }
    
    async def get_case_details(self, key):
        basic_info = self.get_basic_info(key)
        charges_info = self.get_charges_info(key)
        parties_info = self.get_parties_info(key)
        
        case_dict = {
            **basic_info,
            **charges_info,
            **parties_info
        }

        case_dict["court_code"] =case_dict["court_id"]
        case_dict["status"] = "new"
        case_dict["case_date"] = case_dict["court_id"]
        case_dict["charges_description"] = ", ".join([charge.get("charge_desc") for charge in case_dict.get("charges")])
        case_dict["state"] = "NC"
        case_dict["source"] = "North carolina state"
        if case_dict["birth_date"]:
            try:
                case_dict['year_of_birth'] = case_dict['birth_date'].split("/")[0]  
            except:
                case_dict['year_of_birth'] = None
        return case_dict
    
    async def scrape(self):
        last_case_id_nb = self.state.get("last_case_id_nb", 1)
        case_id_nb = last_case_id_nb
        not_found_count = 0
        current_year = datetime.now().year
        
        self.url = "https://portal-nc.tylertech.cloud/Portal/Home/Dashboard/29"
        await self.init_browser()

        while True:
            try:
                if not_found_count > 10:
                    console.log("Too many case_id not found. Ending the search.")
                    break     

                case_id_nb = last_case_id_nb
                case_id_full = f"{str(current_year)[2:]}CR{str(case_id_nb).zfill(6)}"
                last_case_id_nb += 1
                self.state["last_case_id_nb"] = last_case_id_nb
                # self.update_state()

                console.log(f"Current searching case_id-{case_id_full}")

                if self.check_if_exists(case_id_full):
                    console.log(f"Case {case_id_full} already exists. Skipping ...")
                    continue

                case_keys = await self.search_by_case_number(case_id_full)

                if not case_keys:
                    console.log(f"Case {case_id_full} not found. Skipping ...")
                    not_found_count += 1
                    continue
                not_found_count = 0

                console.log("Extracting Case Information...")
                
                for key in case_keys:
                    case_dict = await self.get_case_details(key)
                    self.insert_case(case_dict)
                    console.log(
                        f"Inserted case {case_id_full}"
                    )
                    self.insert_lead(case_dict)
                    console.log(
                        f"Inserted lead {case_id_full}"
                    )
            except Exception as e:
                console.log(f"Failed to scaraping - {e}")
                continue

if __name__ == "__main__":
    ncscraper = NorthCarolinaScraper()
    asyncio.run(ncscraper.scrape())
    console.log("Done running", __file__, ".")