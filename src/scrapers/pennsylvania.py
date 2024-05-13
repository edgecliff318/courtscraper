import asyncio
import os
import re
import sys
import uuid
from pathlib import Path

import pandas as pd
from playwright.async_api import async_playwright
from rich.console import Console

from src.scrapers.base import ScraperBase

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    + "/libraries"
)

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
)

console = Console()

TIMEOUT = 120000
WAIT_TIMEOUT = 7000
PDF_EXTENSION = ".pdf"
REGEX_PATTERNS = {
    "case_id": r"Docket Number: (MJ-\d+-TR-\d+-(\d+))",
    "first_name": r"Name:----.*?, (.*?)----",
    "last_name": r"Name:----(.*?),",
    "city": r"Address\(es\):----Home (.*?),",
    "state": r"Address\(es\):----Home .*?, (.*?)\s",
    "charges_description": r"Grade Description S----(.*?)----",
    "dob": r"Date of Birth:----(.*?)----",
    "address": r"Address\(es\):----Home (.*?)----",
    "case_date": r"Offense Dt\. (.*?)----",
}


class PennsylvaniaScraper(ScraperBase):
    BASE_URL = "https://ujsportal.pacourts.us/CaseSearch"

    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

    async def navigate_to_base_page(self, page):
        try:
            await page.goto(self.BASE_URL, timeout=TIMEOUT)
            console.log(f"Successfully navigated to {self.BASE_URL}")
        except Exception as e:
            console.print(
                f"An error occurred while navigating to {self.BASE_URL}: {str(e)}"
            )

    async def perform_search_by_date(self, page):
        try:
            console.log(
                f"Performing search from {self.start_date} to {self.end_date}"
            )
            await page.locator('select[title="Search By"]').select_option(
                label="Date Filed"
            )
            await page.fill('input[name="FiledStartDate"]', self.start_date)
            await page.fill('input[name="FiledEndDate"]', self.end_date)
            await page.locator("#btnSearch").click()
            await page.wait_for_timeout(WAIT_TIMEOUT)
        except Exception as e:
            console.print(
                f"An error occurred while performing the search: {str(e)}"
            )

    async def download_case_file(self, page, url):
        try:
            file_path = f"{str(uuid.uuid4())}{PDF_EXTENSION}"
            response = await page.request.get(url)
            if response.status == 200:
                console.log(f"File {file_path} created successfully")
                Path(file_path).write_bytes(await response.body())
                return file_path

            else:
                console.print(
                    f"Failed to fetch the case file. Status code: {response.status}"
                )
        except Exception as e:
            console.print(
                f"An error occurred while downloading the case file: {str(e)}"
            )
            return None

    def parse_case_details(self, content):
        details = {}
        try:
            for key, pattern in REGEX_PATTERNS.items():
                match = re.search(pattern, content)
                details[key] = match.group(1) if match else ""
        except Exception as e:
            console.print(
                f"Error occurred while parsing case details: {str(e)}"
            )
        details["charges"] = [
            {
                "charge_description": details["charges_description"],
            }
        ]
        return details

    async def load_pdf_content(self, pdf_file_name: str):
        from unstructured.partition.pdf import partition_pdf

        try:
            pdf_elements = partition_pdf(pdf_file_name)
            combined_content = "----".join(
                [element.text for element in pdf_elements]
            )
            return combined_content
        except FileNotFoundError:
            console.log(f"PDF file {pdf_file_name} not found.")
            return None

    async def get_table_headers(self, page):
        table = await page.query_selector("#caseSearchResultGrid")
        header_table = await table.query_selector("thead > tr")
        columns_elements = await header_table.query_selector_all("th")
        columns = [await column.inner_text() for column in columns_elements]
        mapping = {
            "Docket Number": "case_id",
            "Case Caption": "case_desc",
            "Court Type": "court_type",
            "Filing Date": "filing_date",
            "Primary Participant(s)": "formatted_party_name",
            "Date Of Birth(s)": "birth_date",
            "County": "county",
        }
        return [mapping.get(column, column) for column in columns]

    async def get_case_details_from_row(self, row, columns):
        # Get the case details from the row
        items = await row.query_selector_all("td")
        if not items:
            return {}

        # Iterating cell by cell
        case_details = {}
        for index, item in enumerate(items):
            column_name = columns[index]
            if column_name == "":
                continue
            column_value = await item.inner_text()
            case_details[column_name] = column_value

        # State
        case_details["state"] = "PA"

        # Define year_of_birth
        try:
            case_details["year_of_birth"] = pd.to_datetime(
                case_details["birth_date"]
            ).year

            # Age vs now
            case_details["age"] = (
                pd.to_datetime("now").year - case_details["year_of_birth"]
            )

        except Exception as e:
            console.print(
                f"An error occurred while parsing year of birth: {str(e)}"
            )

        return case_details

    async def process_case_rows(self, page):
        try:
            courts = {}
            rows = await page.query_selector_all("#caseSearchResultGrid tr")
            columns = await self.get_table_headers(page)
            for row in rows:
                # Case the case URL
                case_url = await row.eval_on_selector_all(
                    "a.icon-wrapper",
                    "elements => elements.map(element => element.href ? element.href : null)",
                )

                console.log(f"Case URL: {case_url}")
                if isinstance(case_url, list):
                    if len(case_url) == 0:
                        continue
                    case_url = case_url[0]
                case_details = await self.get_case_details_from_row(
                    row, columns
                )
                case_file_path = await self.download_case_file(page, case_url)
                try:
                    if case_file_path:
                        content = await self.load_pdf_content(case_file_path)
                        if content:
                            # Extract the information from the PDF
                            case_details_pdf = self.parse_case_details(content)
                            case_details.update(case_details_pdf)

                            # Upload the PDF and add it to the case details
                            blob_filepath = f"cases/{case_details['case_id']}/{case_details['case_id']}.pdf"
                            self.upload_file(case_file_path, blob_filepath)
                            case_details["documents"] = [
                                {
                                    "document_title": "Case File",
                                    "file_path": blob_filepath,
                                }
                            ]
                            court_code = f"PA_{case_details.get('county')}"
                            if court_code not in courts.keys():
                                courts[court_code] = {
                                    "code": court_code,
                                    "county_code": case_details.get("county"),
                                    "enabled": True,
                                    "name": f"Pennsylvania, {case_details.get('county')}",
                                    "state": "PA",
                                    "type": "CT",
                                }
                                self.insert_court(courts[court_code])
                            self.insert_case(case_details)
                            self.insert_lead(case_details)

                except Exception as e:
                    console.print(
                        f"An error occurred while processing case rows: {str(e)}"
                    )
                finally:
                    try:
                        if case_file_path and os.path.exists(case_file_path):
                            os.remove(case_file_path)
                            console.log(
                                f"File {case_file_path} removed successfully"
                            )
                    except Exception as e:
                        console.print(
                            f"An error occurred while removing file: {str(e)}",
                            style="bold red",
                        )

        except Exception as e:
            console.print(
                f"An error occurred while processing case rows: {str(e)}"
            )

    async def run_main_process(self, pw):
        browser = None
        try:
            console.log("Launching browser...")
            browser = await pw.chromium.launch(headless=False)
            page = await browser.new_page()
            console.log("Browser launched successfully.")

            console.log("Navigating to page...")
            await self.navigate_to_base_page(page)
            console.log("Navigation to page completed.")

            console.log("Performing search...")
            await self.perform_search_by_date(page)
            console.log("Search completed.")

            console.log("Processing cases...")
            await self.process_case_rows(page)
            console.log("Case processing completed.")

            console.log("Process completed successfully.")
        except Exception as e:
            console.print(
                f"An error occurred during the main process: {str(e)}"
            )
        finally:
            if browser:
                console.log("Closing browser...")
                await browser.close()
                console.log("Browser closed successfully.")

    async def execute_main_process(self):
        try:
            async with async_playwright() as playwright:
                console.log("Starting main process...")
                await self.run_main_process(playwright)
                console.log("Main process completed successfully.")
        except Exception as e:
            console.print(
                f"An error occurred during the execution of the main process: {str(e)}"
            )

    def run(self) -> None:
        try:
            console.log("Starting the scraper...")
            asyncio.run(self.execute_main_process())
            console.log("Scraper completed successfully.")
        except Exception as e:
            console.print(
                f"An error occurred while running the scraper: {str(e)}"
            )


if __name__ == "__main__":
    try:
        console.log("Initializing Pennsylvania Scraper...")
        scraper = PennsylvaniaScraper(
            start_date="2024-05-10", end_date="2024-05-12"
        )
        console.log("Pennsylvania Scraper initialized successfully.")

        console.log("Running Pennsylvania Scraper...")
        scraper.run()
        console.log("Pennsylvania Scraper run completed successfully.")
    except Exception as e:
        console.print(
            f"An error occurred while running the Pennsylvania Scraper: {str(e)}"
        )
