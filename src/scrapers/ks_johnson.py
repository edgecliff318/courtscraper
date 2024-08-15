# Import necessary libraries
import asyncio
import os
import re
from datetime import datetime
from typing import Tuple

from dotenv import load_dotenv
from rich.console import Console

from playwright.async_api import TimeoutError, async_playwright
from src.scrapers.base.scraper_base import ScraperBase

# Configure logging
console = Console()


class KSJohnson(ScraperBase):

    @staticmethod
    def split_race_sex_dob(race_sex_dob: str) -> Tuple[str, str, str]:
        """
        Splits a string containing race, sex, and date of birth into separate components.

        Args:
            race_sex_dob (str): The string containing race, sex, and date of birth.

        Returns:
            Tuple[str, str, str]: A tuple containing the race, sex, and date of birth.
        """
        pattern = r"(?:([A-Za-z]+)\s*)?/([MF]) (\d{2}/\d{2}/\d{2})"
        match = re.match(pattern, race_sex_dob)
        if match:
            return match.group(1), match.group(2), match.group(3)
        return "", "", ""

    @staticmethod
    def check_and_convert_date(date_string: str) -> datetime:
        """
        Attempts to parse a date string into a datetime object using multiple formats.

        Args:
            date_string (str): The date string to be parsed.

        Returns:
            datetime: The parsed datetime object.
        """
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%y",
        ]

        for fmt in formats:
            try:
                date_object = datetime.strptime(date_string, fmt)
                return date_object
            except ValueError:
                continue

        console.log("The string is not in a recognizable datetime format.")
        return None

    @staticmethod    
    def parse_full_address(address_string):  
        # Initialize with default values  
        address_info = {  
            "address_line_1": "UNKNOWN",  
            "address_city": "UNKNOWN",  
            "address_state_code": "UNKNOWN",  
            "address_zip": "00000"  
        }  

        if not isinstance(address_string, str) or not address_string.strip():  
            return address_info  

        # Split components based on commas, avoiding empty parts  
        address_parts = [part.strip() for part in address_string.split(',') if part.strip()]  

        # Attempt to extract ZIP code  
        zip_search = re.search(r'\b\d{5}(?:-\d{4})?\b', address_string)  
        if zip_search:  
            address_info["address_zip"] = zip_search.group(0)  
            address_parts = [part.replace(address_info["address_zip"], '').strip() for part in address_parts]  

        # Attempt to extract state code  
        # Modified statement for state check, ensures it matches only part of the address that stands alone  
        for part in address_parts:  
            state_search = re.search(r'\b([A-Z]{2})\b', part)  
            if state_search and state_search.group(1):  
                address_info["address_state_code"] = state_search.group(1)  
                address_parts = [part.replace(address_info["address_state_code"], '').strip() for part in address_parts]  
                break  # State code found, exit loop  

        # Process remaining parts  
        if len(address_parts) >= 3:  
            address_info["address_line_1"] = address_parts[0]  
            address_info["address_city"] = address_parts[1]  

        elif len(address_parts) == 2:  
            address_info["address_line_1"] = address_parts[0]  
            address_info["address_city"] = address_parts[1]  

        elif len(address_parts) == 1:  
            # Assume single remaining part is the address line if zip and state were extracted confidently  
            if address_info["address_state_code"] != "UNKNOWN" or address_info["address_zip"] != "UNKNOWN":  
                address_info["address_line_1"] = address_parts[0]  
            else:  
                # Fall back assumption: single part without zip/state is city  
                address_info["address_city"] = address_parts[0]  

        return address_info["address_line_1"], address_info["address_city"], address_info["address_state_code"], address_info["address_zip"]   
    
    async def initialize_browser(self, user_name: str, password: str) -> None:
        """
        Initializes the browser and logs into the website.

        Args:
            user_name (str): The username for login.
            password (str): The password for login.
        """
        try:
            URL = "https://www.jococourts.org/"
            console.log("Initialization of Browser...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True, slow_mo=50
            )
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            await self.page.goto(URL)
            await self.page.fill("#MainContent_txtUserID", user_name)
            await self.page.fill("#MainContent_txtPassword", password)
            await self.page.click("#MainContent_btnSubmit")
        except Exception as e:
            console.log(f"Error during browser initialization: {e}")
            raise

    async def search_details(self, case_number: str) -> None:
        """
        Searches for the details of the specified case number.

        Args:
            case_number (str): The case number to search for.
        """
        URL = "https://www.jococourts.org/securepublic/"
        await self.page.goto(URL)
        try:
            await self.page.fill("#txtCaseNo", case_number)
            await self.page.click("#BtnsrchExact")
        except Exception as e:
            console.log(f"Error during search details: {e}")
            raise

    async def get_court_id(self, case_id: str) -> str:
        """
        Retrieves or creates a court ID based on the case ID.

        Args:
            case_id (str): The case ID.

        Returns:
            str: The court ID.
        """
        city_code = "Johnson"
        city_name = "Johnson"
        court_code = f"KS_{city_code}"

        if court_code not in self.courts.keys():
            self.courts[court_code] = {
                "code": court_code,
                "county_code": city_code,
                "enabled": True,
                "name": f"Kansas, {city_name}",
                "state": "KS",
                "type": "TC",
            }
            self.insert_court(self.courts[court_code])
        else:
            console.log(f"{court_code} already exist")
        return court_code

    async def get_case_details(self, case_id) -> dict:
        """
        Fetches the case details from the website.

        Returns:
            dict: A dictionary containing the case details.
        """
        # get court_id
        court_id = ""
        try:
            court_id = await self.get_court_id(case_id)
        except Exception as e:
            console.log("Error while getting court id: ", e)

        # get judge
        judge = ""
        try:
            judge = await self.page.locator(
                "xpath=/html/body/form/table[1]/tbody/tr[2]/td[4]/input"
            ).input_value()
        except Exception as e:
            console.log("Error while getting judge: ", e)

        # get status
        status = ""
        try:
            status = await self.page.locator(
                "xpath=/html/body/form/table[1]/tbody/tr[2]/td[8]/input"
            ).input_value()
        except Exception:
            console.log("Error while getting status: ", e)

        # get last_name
        last_name = ""
        try:
            last_name = await self.page.locator(
                "xpath=/html/body/form/table[1]/tbody/tr[3]/td[2]/input"
            ).input_value()
        except Exception:
            console.log("Error while getting last name: ", e)

        # get first_name
        first_name = ""
        try:
            first_name = await self.page.locator(
                "xpath=/html/body/form/table[1]/tbody/tr[3]/td[4]/input"
            ).input_value()
        except Exception:
            console.log("Error while getting first name: ", e)

        # get middle_name
        middle_name = ""
        try:
            middle_name = await self.page.locator(
                "xpath=/html/body/form/table[1]/tbody/tr[3]/td[6]/input"
            ).input_value()
        except Exception:
            console.log("Error while getting middle name: ", e)

        # get race, sex, dob of defendant
        race_sex_dob = ""
        try:
            race_sex_dob = await self.page.locator(
                "xpath=/html/body/form/table/tbody/tr[4]/td[2]/input"
            ).input_value()
        except Exception:
            console.log("Error while getting race, sex, dob of defendant: ", e)

        # Convert race, sex, dob of defendant
        race, sex, dob = "", "", ""
        try:
            race, sex, dob = self.split_race_sex_dob(race_sex_dob)
        except Exception:
            console.log("Error while converting race, sex, dob of defendant: ", e)
        console.log("race, sex, dob of defendant: ", race, sex, dob)

        # Convert dob to birth_date and year_of_birth
        birth_date = None
        try:
            birth_date = self.check_and_convert_date(dob)
        except Exception:
            console.log("Error while converting dob to birth_date and year_of_birth: ", e)
        
        year_of_birth = ""
        try:
            year_of_birth = birth_date.year if birth_date else ""
        except Exception as e:
            console.log("Error while getting year_of_birth: ", e)

        # Get defendant details
        # Convert case filing date
        original_filling_date = ""
        filling_date = None
        try:
            original_filling_date = await self.page.inner_html(
                "#Form1 > table:nth-child(5) > tbody > tr:nth-child(2) > td:nth-child(3)"
            )
        except Exception:
            original_filling_date = ""
        filling_date = self.check_and_convert_date(original_filling_date)

        # Get sections
        section = ""
        try:
            section = await self.page.inner_html(
                "#Form1 > table:nth-child(5) > tbody > tr:nth-child(2) > td:nth-child(2)"
            )
        except Exception as e:
            console.log("Error while getting section: ", e)

        # Get title
        title = ""
        try:
            title = await self.page.inner_html(
                "#Form1 > table:nth-child(5) > tbody > tr:nth-child(2) > td:nth-child(4)"
            )
        except Exception:
            console.log("Error while getting title: ", e)

        charges = [
            {
                "section": section,
                "date": filling_date,
                "offense_description": title,
            }
        ]

        await self.page.click("#cmdDefendentInfo")

        address = ""
        # Get addrss details
        try:
            address = await self.page.inner_html(
                "body > table > tbody > tr:nth-child(2) > td:nth-child(1)"
            )
        except:
            console.log("Error while getting address: ", e)

        address_line_1, address_city, address_state_code, address_zip = self.parse_full_address(address)
        
        # Create case details dictionary
        case_dict = {
            "case_id": case_id,
            "court_id": court_id,
            "court_code": court_id,
            "last_name": last_name,
            "first_name": first_name,
            "middle_name": middle_name,
            "judge": judge,
            "status": "new",
            "state": "KS",
            "race": race,
            "sex": sex,
            "birth_date": str(birth_date),
            "year_of_birth": year_of_birth,
            "filling_date": filling_date,
            "case_date": filling_date,
            "charges": charges,
            "charges_description": " ".join([item["offense_description"] if item else "" for item in charges]),
            "address_line_1": address_line_1,
            "address_city": address_city,
            "address_state_code": address_state_code,
            "address_zip": address_zip,
            "address": address_line_1,
            "city": address_city,
            "zip_code": address_zip,
            "county": "Johnson",
            "state": "KS",
            "source": "kansas_johnson_county",
        }

        return case_dict
    
    async def scrape(self, search_parameters) -> None:
        """
        Main scraping function that orchestrates the entire scraping process.

        Args:
            search_parameters (dict): The search parameters including username and password.
        """
        console.log("Connecting...")
        user_name = search_parameters.get("username")
        password = search_parameters.get("password")
        # Initialize the browser and login
        await self.initialize_browser(user_name, password)

        # Initialize counters and state
        last_case_id_nb = self.state.get("last_case_id_nb", 1)
        not_found_count = 0

        current_year = datetime.now().year
        self.courts = {}
        while True:
            try:
                if not_found_count > 10:
                    console.log("Too many cases not found. Ending the search.")
                    break

                case_id_nb = last_case_id_nb
                last_case_id_nb += 1

                # Construct the case ID
                case_id_full = (
                    f"{str(current_year)[2:]}TC{str(case_id_nb).zfill(5)}"
                )


                # Check if the case already exists
                if self.check_if_exists(case_id_full):
                    console.log(
                        f"Case {case_id_full} already exists. Skipping ..."
                    )
                    continue
                
                case_dict = {}
                # Search and get case details
                try:
                    await self.search_details(case_id_full)
                    case_dict = await self.get_case_details(case_id_full)
                except Exception as e:
                    console.log(f"Case {case_id_full} not found. Skipping ...", e)
                    not_found_count += 1
                    continue

                console.log("Scraped case_dict successfully!")
                # Update and insert case details
                console.log(f"Inserting case for {case_id_full}...")
                self.insert_case(case_dict)
                console.log(f"Inserting lead for {case_id_full})")
                self.insert_lead(case_dict)
                console.log("Inserted case and lead for ", case_id_full)

                self.state["last_case_id_nb"] = last_case_id_nb
                self.update_state()
                await self.page.wait_for_timeout(2000)
            except TimeoutError:
                console.log("Timeout error. Retrying...")
                await self.page.wait_for_timeout(2000)
            except Exception as e:
                console.log(f"Failed to insert case - {e}")
                continue
