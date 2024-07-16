""" Scraper for Minnesota State """
import asyncio
import re
import time
import os
import pandas as pd

from playwright.async_api import async_playwright, TimeoutError
from datetime import datetime
from tempfile import NamedTemporaryFile
from rich.console import Console

from models.cases import Case
from models.leads import Lead
from src.scrapers.base import ScraperBase

console = Console()

class MinnesotaScraper(ScraperBase):
    field_mapping = {
        "Case Number": "case_id",
        "Case Type": "case_type",
        "Case Title": "description",
        "Date Filed": "filing_date",
        "Case Status": "case_status",
        "Case Location": "case_location", # I did not find any matching for court_id, for now, I map as Case Location
    }

    async def init_browser(self):
        """Initialize the browser."""
        pw = await async_playwright().start()
        # Proxy 9090
        browser = await pw.chromium.launch(
            headless=True,
            # args=["--proxy-server=socks5://localhost:9090"]
        )
        context = await browser.new_context(user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
        page = await context.new_page()
        self.url = 'https://publicaccess.courts.state.mn.us/CaseSearch'
        self.courts = {}
        await page.goto(self.url)
        await page.click("#tcModalAcceptBtn")
        return page

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

    def parse_full_address(self, address_string):  
        address_info = {"address_line_1": 'N/A', "address_city": 'N/A', "address_state_code": 'N/A', "address_zip": 'N/A'}  

        if address_string:  
            # Split components based on comma  
            address_parts = [part.strip() for part in address_string.split(',')]  

            # Find zip by looking for a group of 5 digits  
            zip_search = re.search(r'(\b\d{5}\b)', address_string)  
            if zip_search:  
                address_info["address_zip"] = zip_search.group(0)  
                # remove zip from address_parts if found  
                for i, part in enumerate(address_parts):  
                    if address_info["address_zip"] in part:  
                        address_parts[i] = re.sub(address_info["address_zip"], '', part).strip()  

            # Find state by looking for a group of 2 letters surrounded by whitespace or at start/end of string  
            state_search = re.search(r'(^|(?<=\s))([A-Z]{2})($|(?=\s))', address_string)  
            if state_search:  
                address_info["address_state_code"] = state_search.group(0)  
                # remove state from address_parts if found  
                for i, part in enumerate(address_parts):  
                    if address_info["address_state_code"] in part:  
                        address_parts[i] = re.sub(address_info["address_state_code"], '', part).strip()  

            # If still we have 2 parts assume they are address and city  
            if len(address_parts) == 2:  
                address_info["address_line_1"], address_info["address_city"] = address_parts  

            elif len(address_parts) == 1 and ' ' in address_parts[0]:  # If we are left with a single part containing a space, guess it might address line and city  
                address_info["address_line_1"], address_info["address_city"] = address_parts[0].rsplit(' ', 1)  # separates last word assuming it might be city  

            elif len(address_parts) == 1:  # assume this is the city if only one part left  
                address_info["address_city"] = address_parts[0]  

        return address_info["address_line_1"], address_info["address_city"], address_info["address_state_code"], address_info["address_zip"]
    

    async def search_by_case_number(self, page, case_num):
        """Submit the search form."""
        await page.goto(self.url)
        
        await page.click('a:has-text("Case Number")')
        await page.type('#CaseSearchNumber', case_num, delay=100)
        await page.click('#btnCaseSearch')
        
        await page.click('a:has-text("View Case Details")')
        await page.wait_for_timeout(1500)
    
    async def get_court_id(self, case_dict):
        county_name = case_dict["case_location"].split(' ', 1)[0]  
        county_code = county_name
        court_code = f"MN_{county_code}"

        if court_code not in self.courts:
            self.courts[court_code] = {
                "code": court_code,
                "county_code": county_code,
                "enabled": True,
                "name": f"Minnesota, {county_name}",
                "state": "MN",
                "type": "VB",
                "source": f"MN_{county_name} county",
                "county": county_name
            }
            self.insert_court(self.courts[court_code])

        return court_code

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
    
    async def get_charges_and_court_date(self, page):
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
                    if offense_date:
                        offense_date = offense_date.strip() if offense_date else None
                        offense_date = datetime.strptime(offense_date, "%m/%d/%Y") if offense_date else None
            
            charges.append({
                "description": description,
                "statute": statute,
                "offense_date": offense_date
            })
        return charges, court_date
    
    async def get_extra_case_info(self, page):
        dob = await page.eval_on_selector("span[title='Date of Birth']", "el => el.nextSibling.nextSibling.textContent")  
        dob = dob.strip() if dob else None
        print(f"Defendant DOB: {dob}")  # Defendant DOB  

        name = await page.eval_on_selector("div:has-text('Defendant') span.mpa-text-md:nth-child(2)", "el => el.textContent")  
        name = name.strip() if name else None
        print(f"Defendant name: {name}") 

        address = await page.eval_on_selector(".col-12.col-md-6 > div:nth-child(4) > span","el => el.textContent.trim()")  

        print(f"address: {address}") 
        return dob, name, address

    async def get_cases(self, page):
        basic_info = await self.get_basic_case_info(page)
        parties = await self.get_parties(page)
        charges, court_date = await self.get_charges_and_court_date(page)

        dob, name, address = await self.get_extra_case_info(page)

        year_of_birth = dob.split('/')[-1]  # '-' as separator and selects the last element  
        birth_date = dob

        first_name, middle_name, last_name = self.split_full_name(name)

        address_line_1, address_city, address_state_code, address_zip = self.parse_full_address(address)

        charges_descriptions = [charge["description"] for charge in charges]

        case_dict = {
            value: basic_info.get(key) for key, value in self.field_mapping.items()
        }

        case_dict["court_id"] = await self.get_court_id(case_dict)
        case_dict["court_code"] = await self.get_court_id(case_dict)
                         
        if case_dict.get('filing_date'):
            case_dict['filing_date'] = datetime.strptime(case_dict['filing_date'], "%m/%d/%Y")

        case_dict = {
            **case_dict,
            "parties": parties,
            "charges": charges,
            "charges_descriptions": charges_descriptions,
            "court_date": court_date,
            "year_of_birth": year_of_birth,
            "birth_date": birth_date,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "address_line_1": address_line_1,
            "address_city": address_city,
            "address_state_code": address_state_code,
            "address_zip": address_zip,
            "city": address_city,
            "zip_code": address_zip,
            "state": "MN",
            "source": "Minnesota State",
            "county": case_dict["case_location"].split(' ', 1)[0],
        }
        return case_dict
    
    async def scrape(self):
        """ Main scraping function to handle the entire scraping process. """
        last_case_id_nb = self.state.get("last_case_id_nb", 69261)
        case_id_nb = last_case_id_nb
        not_found_count = 0

        current_year = datetime.now().year
        case_id_full = f"27-VB-{str(current_year)[2:]}-{str(case_id_nb).zfill(5)}"

        page = await self.init_browser()
           
        while True:
            try:
                if not_found_count > 10:
                    console.log("Too many filing dates not found. Ending the search.")
                    break

                case_id_nb = last_case_id_nb
                case_id_full = f"27-VB-{str(current_year)[2:]}-{str(case_id_nb).zfill(5)}"
                last_case_id_nb += 1

                console.log(f"Current searching case_id-{case_id_full}")
                
                case_id = case_dict.get("case_id")
                if self.check_if_exists(case_id):
                    console.log(
                        f"Case {case_id} already exists. Skipping..."
                    )
                    continue
                
                await self.search_by_case_number(page, case_id_full)
                case_dict = await self.get_cases(page)

                if not case_dict:
                    console.log(
                        f"Case {case_id_full} not found. Skipping ..."
                    )
                    not_found_count += 1
                    continue
                
                not_found_count = 0

                console.log("case_dict -", case_dict)
                console.log(f"Inserting case {case_id}...")
                self.insert_case(case_dict)
                console.log(
                    f"Inserted case {case_id_full}"
                )
                self.insert_lead(case_dict)
                console.log(
                    f"Inserted lead {case_id_full}"
                )
                self.state["last_case_id_nb"] = last_case_id_nb
                # self.update_state()
            except Exception as e:
                console.log(f"Error occurred while scraping: {e}")
 
    
if __name__ == "__main__":
    console.log("Minnesota State Scraper")
    minnesotascraper = MinnesotaScraper()
    asyncio.run(minnesotascraper.scrape())
    console.log("Done running", __file__, ".")