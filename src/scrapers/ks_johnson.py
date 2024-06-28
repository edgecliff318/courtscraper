# Import necessary libraries
import asyncio
import os
import os.path
import sys
import re

# Import specific modules from libraries
from playwright.async_api import async_playwright, TimeoutError
from typing import Tuple
from datetime import datetime
from urllib.parse import parse_qs, urljoin, urlparse
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress
from tempfile import NamedTemporaryFile

from src.scrapers.base.scraper_base import ScraperBase

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    + "/libraries"
)

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
)

# Initializing console for logging
console = Console()

# Define the scraper class
class KSJohnson(ScraperBase):
    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        case_id: str | None = None,
    ) -> None:
        self.email = email
        self.password = password
        # TODO change the values
        self.case_id = case_id or "24TC00457"
        super().__init__(email, password)
        console.log(f" we are seaeching for {self.case_id}")

    def split_RaceSexDOB(self, RaceSexDOB):
        # Regular expression pattern to match race, sex, and DOB
        pattern = r"([A-Za-z]+)/([MF]) (\d{2}/\d{2}/\d{2})"
        match = re.match(pattern, RaceSexDOB)
        
        if match:
            race = match.group(1)
            sex = match.group(2)
            dob = match.group(3)
            return race, sex, dob
        else:
            # Return None if the pattern does not match
                return None, None, None
        
    def check_and_convert_date(self, date_string):
        formats = [
            "%Y-%m-%d %H:%M:%S", # Example: "2023-10-04 12:30:45"
            "%Y-%m-%d", # Example: "2023-10-04"
            "%m/%d/%y", # Example: "02/03/23"
            # Add more formats as needed
        ]
        
        for fmt in formats:
            try:
                # Try to parse the string to a datetime object with the given format
                date_object = datetime.strptime(date_string, fmt)
                print(f"Converted to datetime object using format {fmt}: {date_object}")
                return date_object
            except ValueError:
                continue
        
        # If none of the formats work
        print("The string is not in a recognizable datetime format.")
        return None
            
    def parse_full_address(self, full_address: str) -> Tuple[str, str, str, str]:
        """
        Parses a full address string into its components: address_line_1, address_city, 
        address_state_code, and address_zip. If the address does not conform to a US
        format, it tries to extract as much information as possible.
        """
        address_line_1 = ""
        address_city = ""
        address_state_code = ""
        address_zip = ""

        # Attempt to extract address_line_1, city, state_code, and zip using a regex pattern
        pattern = re.compile(
            r'^(?P<address_line_1>[\w\s\#,\.-]+?)[\s,]+'
            r'(?P<address_city>[A-Za-z\s]+?)[\s,]+'
            r'(?P<address_state_code>[A-Z]{2})?[\s,]*'
            r'(?P<address_zip>\d{5}(-\d{4})?|[A-Z0-9 ]{6,10})?$'
        )
        match = pattern.match(full_address.strip())

        if match:
            address_line_1 = match.group('address_line_1').strip() if match.group('address_line_1') else ""
            address_city = match.group('address_city').strip() if match.group('address_city') else ""
            address_state_code = match.group('address_state_code').strip() if match.group('address_state_code') else ""
            address_zip = match.group('address_zip').strip() if match.group('address_zip') else ""
        else:
            # If the full match fails, try to extract from the best matching patterns
            address_part = re.match(r'^(.*?)[\s,]{2}', full_address)
            city_part = re.search(r',\s*([A-Za-z\s]+)\s*,?\s*[A-Z0-9]*', full_address)
            state_zip_part = re.search(r'([A-Z]{2})?\s*(\d{5}(-\d{4})?|[A-Z0-9 ]{6,10})$', full_address.strip())

            if address_part:
                address_line_1 = address_part.group(1).strip()
            if city_part:
                address_city = city_part.group(1).strip()
            if state_zip_part:
                state_part, zip_part = state_zip_part.group(1), state_zip_part.group(2)
                if state_part:
                    address_state_code = state_part.strip()
                if zip_part:
                    address_zip = zip_part.strip()

        return address_line_1, address_city, address_state_code, address_zip
    
    async def initialize_browser(self, user_name, password):
        try:
            URL = 'https://www.jococourts.org/'
            console.log("Initialization of Browser...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False, slow_mo=50)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            await self.page.goto(URL)
            await self.page.fill("#MainContent_txtUserID", user_name)
            await self.page.fill("#MainContent_txtPassword", password)
            await self.page.click("#MainContent_btnSubmit")
        except Exception as e:
            console.log(f"Error during browser initialization: {e}")
            raise

    async def search_details(self, CASE_NUMBER):
        try:
            await self.page.fill("#txtCaseNo", CASE_NUMBER)
            await self.page.click("#BtnsrchExact")
        except Exception as e:
            console.log(f"Error during search details: {e}")
            raise

    async def get_case_details(self):
        
        try:
            case_id = await self.page.locator("xpath=/html/body/form/table[1]/tbody/tr[2]/td[2]/input").input_value()

            courts = {}
            court_code = "KS_Johnson"
            if court_code not in courts.keys():
                courts[court_code] = {
                    "code": court_code,
                    "county_code": "Johnson",
                    "enabled": True,
                    "name": "Kansas, Johnson",
                    "state": "FL",
                    "type": "CT",
                }
                self.insert_court(courts[court_code])
            court_id = court_code

            judge = await self.page.locator("xpath=/html/body/form/table[1]/tbody/tr[2]/td[4]/input").input_value()

            status = await self.page.locator("xpath=/html/body/form/table[1]/tbody/tr[2]/td[8]/input").input_value()    
            
            last_name = await self.page.locator("xpath=/html/body/form/table[1]/tbody/tr[3]/td[2]/input").input_value()           

            first_name = await self.page.locator("xpath=/html/body/form/table[1]/tbody/tr[3]/td[4]/input").input_value()

            middle_name = await self.page.locator("xpath=/html/body/form/table[1]/tbody/tr[3]/td[6]/input").input_value()

            RaceSexDOB = await self.page.locator("xpath=/html/body/form/table/tbody/tr[4]/td[2]/input").input_value()

            race, sex, dob = self.split_RaceSexDOB(RaceSexDOB)

            month, day, year = dob.split('/')

            # Convert the year to four digits (assuming 1900-1999 for years like '69')
            year = '19' + year if int(year) > 50 else '20' + year

            # Construct birth_date string in format 'YYYY-MM-DD'
            birth_date = f"{year}-{month}-{day}"

            # Year of birth as string
            year_of_birth = year

            original_filling_date = await self.page.inner_html("#Form1 > table:nth-child(5) > tbody > tr:nth-child(2) > td:nth-child(3)")
            filling_date = self.check_and_convert_date(original_filling_date)
    
            section = await self.page.inner_html("#Form1 > table:nth-child(5) > tbody > tr:nth-child(2) > td:nth-child(2)")

            title = await self.page.inner_html("#Form1 > table:nth-child(5) > tbody > tr:nth-child(2) > td:nth-child(4)")

            charges = []
            charge = {"section": section, "date": filling_date, "title": title}
            charges.append(charge)

            await self.page.click("#cmdDefendentInfo")

            address = await self.page.inner_html("body > table > tbody > tr:nth-child(2) > td:nth-child(1)")
            address_line_1, address_city, address_state_code, address_zip = self.parse_full_address(address)
            print("case_dict")
            
            case_dict = {
                "case_id": case_id,
                "court_id": court_id,
                "last_name": last_name,
                "first_name": first_name,
                "middle_name": middle_name,
                "judge": judge,
                "status": status,
                "race": race,
                "sex": sex,
                "birth_date": birth_date,
                "year_of_birth": year_of_birth,
                "filling_date": filling_date,
                "charges": charges,
                "address_line_1": address_line_1,
                "address_city": address_city,
                "address_state_code": address_state_code,
                "address_zip": address_zip
            }

            return case_dict

        except Exception as e:
            console.log(f"Error during getting case details: {e}")
            raise

    async def scrape(self, search_parameters):
        case_id = search_parameters["case_id"]
        user_name = search_parameters["user_name"]
        password = search_parameters["password"]

        await self.initialize_browser(user_name, password)
        await self.search_details(case_id)
        case_dict = await self.get_case_details()
        print(case_dict)

        with NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as f:
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

                progress.update(task, advance=1)
        
            await self.browser.close()


if __name__ == "__main__":
    load_dotenv()
    search_parameters = {
        "user_name" : "30275",
        "password" : "TTDpro2024TTD!"
    }
    ks_johnson_scraper = KSJohnson()
    asyncio.run(ks_johnson_scraper.scrape(search_parameters))
    console.log("Done running", __file__, ".")
