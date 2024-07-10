import asyncio
import os
from datetime import datetime
import re
from playwright.async_api import async_playwright, TimeoutError
from rich.console import Console
from models.cases import Case
from models.leads import Lead
from src.scrapers.base.scraper_base import ScraperBase
from twocaptcha import TwoCaptcha

TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')

console = Console()

def get_solver():
    return TwoCaptcha(TWOCAPTCHA_API_KEY)

class DistrictCourtScraper(ScraperBase):
    FIELD_MAPPING = {
        "CaseNumber": "case_id",
        "Name": "name",
        "Address": "address_line_1",
        "Court": "court_id",
        "Charges": "charges",
        "FiledDate": "filing_date",
        "Status": "status",
        "Locality": "location",
        "DOB": "birth_date"
    }
    
    def __init__(self):
        super().__init__()
        self.courts = {}
        self.solver = get_solver()
    
    @staticmethod
    def split_full_name(name):
        parts = re.split(r'[\s,\-\.]+', name)
        first_name = middle_name = last_name = ''
        if len(parts) > 2:
            first_name = parts[0]
            middle_name = ' '.join(parts[1:-1])
            last_name = parts[-1]
        elif len(parts) == 2:
            first_name, last_name = parts
        elif len(parts) == 1:
            first_name = parts[0]
        return first_name, middle_name, last_name
    
    async def init_browser(self):
        console.log("Initiating Browser...")
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
            console.log("The 'Accept' button was not found.")
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(2000)
    
    async def get_courts(self):
        console.log("Getting courts...")
        court_names = await self.page.query_selector_all("input[name='courtName']")
        court_ids = await self.page.query_selector_all("input[name='courtFips']")
        courts = [{"court_id": await court_id.get_attribute("value"), "court_desc": await court_name.get_attribute("value")}
                  for court_id, court_name in zip(court_ids, court_names)]
        return courts
    
    async def get_court_id(self, court_number):
        courts = await self.get_courts()
        court_code = courts[court_number]["court_id"]
        court_desc = courts[court_number]['court_desc']
        # console.log(f"courts-{courts}")

        if court_code not in self.courts:
            self.courts[court_code] = {
                "code": court_code,
                "county_code": court_desc,
                "enabled": True,
                "name": f"Virginia, {court_desc}",
                "state": "VA",
                "type": "TI",
            }
            self.insert_court(self.courts[court_code])

        return court_code

    async def search_case_number(self, case_number, court_id):
        url = f"https://eapps.courts.state.va.us/gdcourts/criminalCivilCaseSearch.do?fromSidebar=true&formAction=searchLanding&searchDivision=T&searchFipsCode={court_id}&curentFipsCode={court_id}"
        await self.page.goto(url)
        search_case_element = await self.page.query_selector("#displayCaseNumber")
        await search_case_element.fill(case_number)  # type: ignore
        submit_button = await self.page.query_selector('input.submitBox')
        if submit_button:
            await submit_button.click()
        else:
            console.log("The 'btnSearch' button was not found.")
        await self.page.wait_for_load_state("networkidle")
    
    async def extract_info(self):
        eliminate_key = [':', '\n', '\t', '\xa0']
        
        # Extract case information
        case_row = await self.page.query_selector("#toggleCase")
        table = await case_row.query_selector("table")  # type: ignore
        tds = await table.query_selector_all("td")  # type: ignore
        
        case_row_dict = {}
        for i in range(0, len(tds), 2):
            key = await tds[i].text_content()
            value = await tds[i + 1].text_content()
            if key and value:
                for element in eliminate_key:
                    key = key.replace(element, "").strip()  # type: ignore
                    value = value.replace(element, "").strip()  # type: ignore
                case_row_dict[key] = value
        
        # Extract charge information
        charge_row = await self.page.query_selector("#toggleCharge")
        table = await charge_row.query_selector("table")  # type: ignore
        tds = await table.query_selector_all("td")  # type: ignore
        
        charge_row_dict = {}
        for i in range(0, len(tds), 2):
            key = await tds[i].text_content()
            value = await tds[i + 1].text_content()
            if key and value:
                key = key.replace(":", "").strip()  # type: ignore
                value = value.replace(":", "").strip()  # type: ignore
                charge_row_dict[key] = value
        
        charges = [{"description": charge_row_dict.get("Charge"), "offense_date": charge_row_dict.get("Offense date")}]
        
        return {**case_row_dict, "charges": charges}
    
    async def scrape(self):
        last_case_id_nb = self.state.get("last_case_id_nb", 1000)
        not_found_count = 0
        current_year = datetime.now().year
        await self.init_browser()
        courts = await self.get_courts()
        while not_found_count <= 10:
            try:
                case_id_full = f"GT{str(current_year)[2:]}00{str(last_case_id_nb).zfill(4)}-00"
                last_case_id_nb += 1
                console.log(f"Current searching case_id-{case_id_full}")
                if self.check_if_exists(case_id_full):
                    console.log(f"Case {case_id_full} already exists. Skipping ...")
                    continue
                
                for court_number in range(len(courts)):
                    court_id = await self.get_court_id(court_number)
                    console.log(f"court_id-{court_id}")
                    await self.search_case_number(case_id_full, court_id)
                    case_dict = await self.extract_info()
                    case_dict = {self.FIELD_MAPPING.get(key, key): value for key, value in case_dict.items() if value is not None}
                    first_name, middle_name, last_name = self.split_full_name(case_dict.get("name", ""))
                    case_dict.update({"court_id": court_id, "first_name": first_name, "middle_name": middle_name, "last_name": last_name})
                    if not case_dict:
                        console.log(f"Case {case_id_full} not found. Skipping ...")
                        not_found_count += 1
                        continue
                    console.log(f"Inserting case {case_id_full}...")
                    self.insert_case(case_dict)
                    self.insert_lead(case_dict)
                    self.state["last_case_id_nb"] = last_case_id_nb
            except TimeoutError:
                console.log("Timeout error. Retrying...")
                await self.page.wait_for_timeout(2000)
                await self.browser.close()
                await self.init_browser()
            except Exception as e:
                console.log(f"Failed to insert case - {e}")
                continue
            console.log(f"court_id-{court_id}")
            court_number += 1
                
if __name__ == "__main__":
    district_court_scraper = DistrictCourtScraper()
    asyncio.run(district_court_scraper.scrape())
    console.log("Done running", __file__, ".")