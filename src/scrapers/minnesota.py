from playwright.async_api import async_playwright, TimeoutError
import pandas as pd
from models.cases import Case
from datetime import datetime
from tempfile import NamedTemporaryFile
from rich.console import Console
from models.leads import Lead
from src.models.cases import Case
from src.models.leads import Lead
from src.scrapers.base import InitializedSession, NameNormalizer, ScraperBase
from rich.progress import Progress
import re
import time
import os
from dotenv import load_dotenv
from twocaptcha import TwoCaptcha
load_dotenv(dotenv_path='.env')
TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')

console = Console()

class MinnesotaScraper(ScraperBase):
    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)
    field_mapping = {
        "Case Number": "case_id",
        "Case Type": "case_type",
        "Case Title": "description",
        "Date Filed": "filing_date",
        "Case Status": "case_status",
        "Case Location": "court_id", # I did not find any matching for court_id, for now, I map as Case Location
    }

    async def init_browser(self):
        """Initialize the browser."""
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
        page = await context.new_page()
        
        return page, browser

    async def search_by_case_number(self, page, case_num):
        """Submit the search form."""
        self.url = 'https://publicaccess.courts.state.mn.us/CaseSearch'
        await page.goto(self.url)
        await page.click("#tcModalAcceptBtn")
        
        await page.click('a:has-text("Case Number")')
        await page.type('#CaseSearchNumber', case_num, delay=100)
        await page.click('#btnCaseSearch')
        
        await page.click('a:has-text("View Case Details")')
        await page.wait_for_timeout(1500)
    
    async def scrape(self, search_parameters):
        page, browser = await self.init_browser()
        case_num = search_parameters['case_id']
        await self.search_by_case_number(page, case_num)
        basic_info = await self.get_basic_case_info(page)
        parties = await self.get_parties(page)
        charges, court_date = await self.get_charges(page)
        case_dict = {
            value: basic_info.get(key) for key, value in self.field_mapping.items()
        }
        case_dict = {
            **case_dict,
            "parties": parties,
            "charges": charges,
            "court_date": court_date
        }

        if case_dict.get('filing_date'):
            case_dict['filing_date'] = datetime.strptime(case_dict['filing_date'], "%m/%d/%Y")
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
                case = Case(**case_dict)
                lead = Lead(**case_dict)
                self.insert_case(case)
                self.insert_lead(lead)

            progress.update(task, advance=1)
       
        await browser.close()
    
    async def get_basic_case_info(self, page):
        caseInfoDiv = await page.query_selector("#CaseInformation")
        case_dict = {}
        if not caseInfoDiv:
            return case_dict
        div = await caseInfoDiv.query_selector('div.col-md-8')
        attributes = await div.query_selector_all('div') if div else []
        for attribute in attributes:
            spans = await attribute.query_selector_all('span')
            key = await spans[0].text_content()
            key = key.strip().replace(":", "") if key else None
            value = await spans[1].text_content()
            case_dict[key] = value
        return case_dict
    
    async def get_parties(self, page):
        party_div = await page.query_selector("#PartyInformation")
        if not party_div:
            return []
        parties_divs = await party_div.query_selector_all("div.mpa-case-details-party-item")
        parties = []
        for party_div in parties_divs:
            div = await party_div.query_selector("div.col-12")
            contents = await div.query_selector_all("div") if div else []
            contents = [await content.text_content() for content in contents]
            if len(contents) > 1:
                parties.append({
                    "role": contents[0].lower().strip() if contents[0] else None,
                    "name": contents[1].strip() if contents[1] else None
                })
        return parties
    
    async def get_charges(self, page):
        charges_div = await page.query_selector("#Charges")
        if not charges_div:
            return None, None
        
        charges_div = await charges_div.query_selector("div.mpa-case-search-charges-wrapper")

        court_date_div = await charges_div.query_selector("div") if charges_div else None
        text = await court_date_div.text_content() if court_date_div else None
        text = text.strip() if text else ""
        court_date = text.split("\n")[1].strip()
        court_date = datetime.strptime(court_date, "%m/%d/%Y") if court_date else None

        charges = []
        charges_divs = await charges_div.query_selector_all("div.mpa-case-search-charge-item-wrapper") if charges_div else []
        for charge_div in charges_divs:
            description_div = await charge_div.query_selector("div.mpa-case-search-charge-charge")
            description_div = await charge_div.query_selector("span")
            description = await description_div.text_content() if description_div else None
            description = description.strip() if description else None
            
            divs = await charge_div.query_selector_all("div.col-12")
            for div in divs:
                spans = await div.query_selector_all("span:not(.sr-only)")
                key = await spans[0].text_content() if spans else None
                key = key.lower().strip().replace(":", "") if key else None
                if key == "statute":
                    statute = await spans[1].text_content() if spans else None
                    statute = statute.strip() if statute else None
                elif key == "offense date":
                    offense_date = await spans[1].text_content() if spans else None
                    offense_date = offense_date.strip() if offense_date else None
                    offense_date = datetime.strptime(offense_date, "%m/%d/%Y") if offense_date else None
                elif key == "disposition date":
                    disposition_date = await spans[1].text_content() if spans else None
                    disposition_date = disposition_date.strip() if disposition_date else None
                    disposition_date = datetime.strptime(disposition_date, "%m/%d/%Y") if disposition_date else None
                elif key == "disposition":
                    disposition = await spans[1].text_content() if spans else None
                    disposition = disposition.strip() if disposition else None
            
            charges.append({
                "description": description,
                "statute": statute,
                "offense_date": offense_date,
                "disposition_date": disposition_date,
                "disposition": disposition
            })
        
        return charges, court_date