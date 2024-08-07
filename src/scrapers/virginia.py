import asyncio
import re
from datetime import datetime, timedelta

from rich.console import Console

from playwright.async_api import async_playwright
from src.callbacks.manage import court
from src.scrapers.base.scraper_base import ScraperBase

console = Console()


class VirginiaScraper(ScraperBase):
    FIELD_MAPPING = {
        "CaseNumber": "case_id",
        "Name": "name",
        "Address": "address",
        "Court": "court_id",
        "Charges": "charges",
        "FiledDate": "filing_date",
        "Status": "status",
        "Locality": "location",
        "DOB": "birth_date",
        "Gender": "sex",
        "Race": "race",
    }

    def __init__(self):
        super().__init__()
        self.courts = {}

    def to_datetime(self, date_str):
        if date_str is None:
            return None
        else:
            return datetime.strptime(date_str, "%m/%d/%Y")

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
        address_info = {
            "address_line_1": "N/A",
            "address_city": "N/A",
            "address_state_code": "N/A",
            "address_zip": "N/A",
        }

        if address_string:
            # Split components based on comma
            address_parts = [
                part.strip() for part in address_string.split(",")
            ]

            # Find zip by looking for a group of 5 digits
            zip_search = re.search(r"(\b\d{5}\b)", address_string)
            if zip_search:
                address_info["address_zip"] = zip_search.group(0)
                # remove zip from address_parts if found
                for i, part in enumerate(address_parts):
                    if address_info["address_zip"] in part:
                        address_parts[i] = re.sub(
                            address_info["address_zip"], "", part
                        ).strip()

            # Find state by looking for a group of 2 letters surrounded by whitespace or at start/end of string
            state_search = re.search(
                r"(^|(?<=\s))([A-Z]{2})($|(?=\s))", address_string
            )
            if state_search:
                address_info["address_state_code"] = state_search.group(0)
                # remove state from address_parts if found
                for i, part in enumerate(address_parts):
                    if address_info["address_state_code"] in part:
                        address_parts[i] = re.sub(
                            address_info["address_state_code"], "", part
                        ).strip()

            # If still we have 2 parts assume they are address and city
            if len(address_parts) == 2:
                (
                    address_info["address_line_1"],
                    address_info["address_city"],
                ) = address_parts

            elif (
                len(address_parts) == 1 and " " in address_parts[0]
            ):  # If we are left with a single part containing a space, guess it might address line and city
                (
                    address_info["address_line_1"],
                    address_info["address_city"],
                ) = address_parts[0].rsplit(
                    " ", 1
                )  # separates last word assuming it might be city

            elif (
                len(address_parts) == 1
            ):  # assume this is the city if only one part left
                address_info["address_city"] = address_parts[0]

        return (
            address_info["address_line_1"],
            address_info["address_city"],
            address_info["address_state_code"],
            address_info["address_zip"],
        )

    async def init_browser(self):
        console.log("Initiating Browser...")
        pw = await async_playwright().start()
        # Proxy 9090
        self.browser = await pw.chromium.launch(
            headless=True,
            # args=["--proxy-server=socks5://localhost:9090"]
        )
        context = await self.browser.new_context()
        self.page = await context.new_page()
        self.url = "https://eapps.courts.state.va.us/gdcourts/landing.do"
        await self.page.goto(self.url)
        await self.page.wait_for_timeout(2000)
        accept_button = await self.page.query_selector("input.submitBox")
        if accept_button:
            await accept_button.click()
        else:
            console.log("The 'Accept' button was not found.")
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(2000)

    async def get_courts(self):
        console.log("Getting courts...")
        court_names = await self.page.query_selector_all(
            "input[name='courtName']"
        )
        court_ids = await self.page.query_selector_all(
            "input[name='courtFips']"
        )
        courts = [
            {
                "court_id": await court_id.get_attribute("value"),
                "court_desc": await court_name.get_attribute("value"),
            }
            for court_id, court_name in zip(court_ids, court_names)
        ]
        return courts

    async def get_court_id(self, court_number):
        courts = await self.get_courts()
        court_code = courts[court_number]["court_id"]
        court_desc = courts[court_number]["court_desc"]

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
        search_case_element = await self.page.query_selector(
            "#displayCaseNumber"
        )
        await search_case_element.fill(case_number)  # type: ignore
        submit_button = await self.page.query_selector("input.submitBox")
        if submit_button:
            await submit_button.click()
        else:
            console.log("The 'btnSearch' button was not found.")
        await self.page.wait_for_load_state("networkidle")

    async def extract_info(self):
        eliminate_key = [":", "\n", "\t", "\xa0"]

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

        charges = [{key: value} for key, value in charge_row_dict.items()]

        return {**case_row_dict, "charges": charges}

    async def find_last_case_nb(self, court_id):
        # Increment the case id by 1000, 100, 10, 1 until finding a valid case id beyond 10/07/2024
        target_date = datetime(year=2024, day=10, month=7)

        # Start at 1st january 2024
        date = datetime(year=2024, day=1, month=1)
        start_date = datetime(year=2024, day=1, month=1)

        # Initial number
        number = 100

        # Reverse
        reverse_check = False

        while date < target_date:
            case_id = f"GT{str(date.year)[2:]}{str(number).zfill(6)}-00"
            console.log(f"Searching for case_id-{case_id}")
            try:
                await self.search_case_number(case_id, court_id)
                case_dict = await self.extract_info()
            except:
                console.log(f"Case {case_id} not found. Skipping ...")
                case_dict = {}

            date = case_dict.get("FiledDate")
            date = datetime.strptime(date, "%m/%d/%Y") if date else None

            # Speed

            if (
                reverse_check
                and date is not None
                and target_date - date <= timedelta(days=20)
            ):
                console.log("Found the date. Stopping the search.")
                break

            if (
                reverse_check
                and date is not None
                and target_date - date >= timedelta(days=20)
            ):
                number += 10
                reverse_check = False

            if date is not None and number == 100:
                speed = number / (date - start_date).days
                console.log(f"Speed: {speed} case per day")
                expected_number = int((target_date - date).days * speed)
                console.log(f"Expected number: {expected_number}")
                number = expected_number
                continue

            if date is None and number == 100:
                console.log("Empty date. Stop the search.")
                number = 1
                self.state[court_id] = number
                self.update_state()
                break

            if date is None:
                console.log("Date is None. Decrementing the number.")
                number -= 100
                date = datetime(year=2024, day=1, month=1)
                reverse_check = True
                continue

            # If more than 1 month increment by 1000
            if date is not None and target_date - date >= timedelta(days=1):
                console.log("More than 1 month. Incrementing by 1000")
                number += 1000

        self.state[court_id] = number
        self.update_state()
        console.log(f"Last case number {number} for court_id-{court_id}")

    async def scrape(self):
        await self.init_browser()
        courts = await self.get_courts()

        for court_number in range(0, len(courts)):
            console.log("court_number", court_number)
            court_id = await self.get_court_id(court_number)
            console.log(f"Current court_id-{court_id}")
            not_found_count = 0
            current_year = datetime.now().year
            last_case_id_nb = self.state.get(court_id, None)

            if last_case_id_nb is None:
                await self.find_last_case_nb(court_id)
                last_case_id_nb = self.state.get(court_id, None)

            while True:
                try:
                    if not_found_count > 10:
                        console.log(
                            "Too many case idsnot found. Ending the search."
                        )
                        break

                    case_id_full = f"GT{str(current_year)[2:]}{str(last_case_id_nb).zfill(6)}-00"

                    console.log(f"Current searching case_id-{case_id_full}")

                    if self.check_if_exists(case_id_full):
                        console.log(
                            f"Case {case_id_full} already exists. Skipping ..."
                        )
                        last_case_id_nb += 1
                        self.state[court_id] = last_case_id_nb
                        self.update_state()
                        continue

                    await self.search_case_number(case_id_full, court_id)

                    case_dict = await self.extract_info()
                    case_dict = {
                        self.FIELD_MAPPING.get(key, key): value
                        for key, value in case_dict.items()
                        if value is not None
                    }

                    filing_date = case_dict.get("filing_date")
                    case_dict["filing_date"] = self.to_datetime(filing_date)
                    case_dict["case_date"] = self.to_datetime(filing_date)

                    first_name, middle_name, last_name = self.split_full_name(
                        case_dict.get("name", "")
                    )
                    case_dict["charges_description"] = case_dict.get(
                        "charges", []
                    )[0].get("Charge", "")

                    (
                        address_line_1,
                        address_city,
                        address_state_code,
                        address_zip,
                    ) = self.parse_full_address(case_dict.get("address", ""))

                    case_dict.update(
                        {
                            "court_id": court_id,
                            "court_code": court_id,
                            "first_name": first_name,
                            "middle_name": middle_name,
                            "last_name": last_name,
                            "address_line_1": address_line_1,
                            "address_city": address_city,
                            "address_state_code": address_state_code,
                            "address_zip": address_zip,
                            "address": address_line_1,
                            "city": address_city,
                            "zip_code": address_zip,
                            "status": "new",
                            "state": "VA",
                            "source": "Virginia District Court",
                        }
                    )

                    if not case_dict:
                        console.log(
                            f"Case {case_id_full} not found. Skipping ..."
                        )
                        not_found_count += 1
                        continue

                    filing_date_parsed = datetime.strptime(
                        filing_date, "%m/%d/%Y"
                    )

                    if filing_date_parsed < datetime(
                        year=2024, day=1, month=4
                    ):
                        console.log(
                            f"Case {case_id_full} is beyond the target date. Ending the search."
                        )
                        break

                    not_found_count = 0

                    console.log(f"Inserting case {case_id_full}...")
                    self.insert_case(case_dict)

                    console.log(f"Inserted case {case_id_full}")
                    self.insert_lead(case_dict)
                    
                    console.log(
                        f"Inserted lead {case_id_full} - Date {filing_date}"
                    )
                    self.state[court_id] = last_case_id_nb + 1
                    self.update_state()
                except Exception as e:
                    console.log(f"Failed to scraping - {e}")
                    last_case_id_nb += 1
                    not_found_count += 1
                    continue


if __name__ == "__main__":
    virginiascraper = VirginiaScraper()
    asyncio.run(virginiascraper.scrape())
    console.log("Done running", __file__, ".")
