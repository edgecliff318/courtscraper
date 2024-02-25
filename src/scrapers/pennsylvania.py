import asyncio
import os
import os.path
import re
import sys
import uuid

from playwright.async_api import async_playwright
from rich.console import Console

from src.scrapers.base import ScraperBase

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir) + "/libraries"
)

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

console = Console()

TIMEOUT = 120000
WAIT_TIMEOUT = 7000
PDF_EXTENSION = ".pdf"
# regex
CASE_ID_REGEX = r"Docket Number: (MJ-\d+-TR-\d+-(\d+))"
FIRST_NAME_REGEX = r"Name:----.*?, (.*?)----"
LAST_NAME_REGEX = r"Name:----(.*?),"
CITY_REGEX = r"Address\(es\):----Home (.*?),"
STATE_REGEX = r"Address\(es\):----Home .*?, (.*?)\s"
CHARGES_DESCRIPTION_REGEX = r"Grade Description S----(.*?)----"
DATE_OF_BIRTH_REGEX = r"Date of Birth:----(.*?)----"
ADDRESS_REGEX = r"Address\(es\):----Home (.*?)----"
CASE_DATE_REGEX = r"Offense Dt\. (.*?)----"


class Pennsylvania(ScraperBase):
    BASE_URL = "https://ujsportal.pacourts.us/CaseSearch"

    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

    async def navigate_to_page(self, page):
        await page.goto(self.BASE_URL, timeout=TIMEOUT)
        console.log(f"Navigated to page {self.BASE_URL} successfully")

    async def perform_search(self, page, start_date, end_date):
        console.log(f"Performing search for {start_date} to {end_date}")
        await page.locator('select[title="Search By"]').select_option(
            label="Date Filed"
        )
        await page.fill('input[name="FiledStartDate"]', start_date)
        await page.fill('input[name="FiledEndDate"]', end_date)
        await page.locator("#btnSearch").click()
        await page.wait_for_timeout(WAIT_TIMEOUT)

    async def generate_case_file(self, page, url: str) -> str | None:
        try:
            file_uuid = str(uuid.uuid4())
            name_file = f"{file_uuid}{PDF_EXTENSION}"
            response = await page.request.get(url)
            if response.status == 200:
                content = await response.body()
                with open(name_file, "wb") as file:
                    file.write(content)
                console.log("File created successfully")
            else:
                console.log("Failed to create file")

            return name_file
        except Exception as e:
            console.log(f"An error occurred while creating the file: {str(e)}")
            return None

    async def load_case_file(self, file_name: str):
        from unstructured.partition.pdf import partition_pdf

        try:
            elements = partition_pdf(file_name)
            content = "----".join([element.text for element in elements])
            return content
        except FileNotFoundError:
            console.log(f"File {file_name} not found.")
            return None

    async def fetch_case_urls(self, row_cells):
        case_urls = []
        try:
            for cell in row_cells:
                url = await cell.eval_on_selector_all(
                    "a.icon-wrapper",
                    "elements => elements.map(element => element.href)",
                )
                if url:
                    case_urls.append(url[0])
        except Exception as e:
            print(f"An error occurred while fetching case URLs: {e}")
        return case_urls

    def extract_with_pattern(self, pattern, input_text, default_value=""):
        try:
            matched_pattern = re.search(pattern, input_text)
            return matched_pattern.group(1) if matched_pattern else default_value
        except Exception as e:
            print(f"An error occurred while extracting with pattern: {e}")
            return default_value

    def extract_case_details(self, case_text):
        try:
            case_details = {
                "case_id": self.extract_with_pattern(CASE_ID_REGEX, case_text),
                "first_name": self.extract_with_pattern(FIRST_NAME_REGEX, case_text),
                "last_name": self.extract_with_pattern(LAST_NAME_REGEX, case_text),
                "city": self.extract_with_pattern(CITY_REGEX, case_text),
                "state": self.extract_with_pattern(STATE_REGEX, case_text),
                "charges_description": self.extract_with_pattern(
                    CHARGES_DESCRIPTION_REGEX, case_text
                ),
                "date_of_birth": self.extract_with_pattern(
                    DATE_OF_BIRTH_REGEX, case_text
                ),
                "address": self.extract_with_pattern(ADDRESS_REGEX, case_text),
                "case_date": self.extract_with_pattern(CASE_DATE_REGEX, case_text),
            }

            return case_details
        except Exception as e:
            print(f"An error occurred while extracting case details: {e}")
            return None

    async def extract_table_data(self, page):
        table = await page.query_selector("#caseSearchResultGrid")
        rows = await table.query_selector_all("tr")
        return rows

    async def process_case_data(self, webpage, case_rows):
        case_urls = await self.fetch_case_urls(case_rows)
        console.log(f"Case URLs length: {len(case_urls)}")
        case_urls = case_urls[:2]
        try:
            for case_url in case_urls:
                case_file = await self.generate_case_file(webpage, case_url)
                case_content = await self.load_case_file(case_file)
                case_data = self.extract_case_details(case_content)
                print(case_data)
        except Exception as e:
            console.log(f"An error occurred while processing case data: {str(e)}")

    async def main(self):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                console.log("Browser opened")
                await self.navigate_to_page(page)
                await self.perform_search(page, self.start_date, self.end_date)
                rows = await self.extract_table_data(page)
                await self.process_case_data(page, rows)
                await browser.close()
        except Exception as e:
            console.log(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    scraper = Pennsylvania(start_date="2024-02-20", end_date="2024-02-24")
    asyncio.run(scraper.main())
