""" Scraper for Maryland General Court """

import asyncio
import os
import re
from datetime import datetime, timedelta

import pandas as pd
import requests
from commonregex import CommonRegex
from rich.console import Console
from tika import parser

from src.core.config import get_settings
from src.scrapers.base.scraper_base import ScraperBase

# Configure logging
console = Console()
settings = get_settings()


class MDScraper(ScraperBase):
    def __init__(self):
        super().__init__()
        self.courts = {}
        self.browser = None
        self.page = None
        self.url = "https://www.mdcourts.gov/mdec/publiccases"

    def is_valid_number(self, x):
        return any(char.isdigit() for char in x) and any(
            char.isalpha() for char in x
        )

    def to_datetime(self, date_str):
        if date_str is None:
            return None
        else:
            return datetime.strptime(date_str, "%m/%d/%Y")

    def get_court_id(self, address_county):
        county_name = address_county
        county_code = address_county
        court_code = f"MD_{county_name}"

        if court_code not in self.courts:
            self.courts[court_code] = {
                "code": court_code,
                "county_code": county_code,
                "enabled": True,
                "name": f"Maryland, {county_name}",
                "state": "MD",
                "type": "GC",
                "source": "Maryland General",
                "county": county_name,
            }
            self.insert_court(self.courts[court_code])

        return court_code

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

    def extract_records(self, page):
        """
        Recursive function to Fetch all records and return
        """
        # identify each record
        records_pattern = r"([\dA-Z-]{7,})\s"
        for t in re.finditer(records_pattern, page):
            if not t:
                continue
            number_pattern = r"[\dA-Z-]{7,}"
            # match if this really is number
            match = re.match(number_pattern, t.group(1))
            if match:
                number = match.group(0)
                if self.is_valid_number(number):
                    new_page = page[page.index(number) + len(number) :]
                    x, y = self.extract_records(new_page)
                    if any((x, y)):
                        next_record = (
                            f"{number}|||{new_page[:new_page.index(x):]}$$${y}"
                        )
                    else:
                        # on last page slice text the remaining text and append number
                        next_record = f"{number}|||{page[page.index(number) + len(number) :]}"

                    return (number, next_record)
        # return null if no match found means we are on last section
        return (0, 0)

    def clean_text(self, text):
        # Remove more than 1 consecutive space
        text = re.sub(r" +", " ", text)
        # Remove more than 1 consecutive newline character
        text = re.sub(r"\n+", "\n", text)
        return text.strip()

    def extract_data_points(self, record):
        case_dict = {}
        citation_splits = record.split("Citation")
        console.log(f"Processing record: {record}")
        cr = CommonRegex(record)
        try:
            case_id_name_splits = citation_splits[0].split("|||")
            case_dict["case_id"] = case_id_name_splits[0].strip()
            name = case_id_name_splits[1].strip()
            first_name, middle_name, last_name = self.split_full_name(name)
            case_dict["first_name"] = first_name
            case_dict["middle_name"] = middle_name
            case_dict["last_name"] = last_name
        except Exception as e:
            console.log(f"Error in extracting case_id and name: {e}")
            case_dict["first_name"] = "N/A"
            case_dict["middle_name"] = "N/A"
            case_dict["last_name"] = "N/A"
            case_dict["name_error"] = True

        try:
            dates = cr.dates
            case_dict["filing_date"] = self.to_datetime(dates[0])

        except Exception as e:
            console.log(f"Error in extracting filing_date: {e}")
            case_dict["filing_date"] = None
            case_dict["filing_date_error"] = True

        try:
            try:
                # complete address
                addresses = cr.street_addresses
                address_line_1 = addresses[0]
                # Get the data between the address and charges
                address_city_zip = record.split(address_line_1)[1].split(
                    "Charges:"
                )[0]
            except Exception as e:
                # Split between Defendqnt Address: and Charges
                address_text = record.split("Defendant Address:")[1].split(
                    "Charges:"
                )[0]
                # Remove trailing \n and beginning \n
                address_text = address_text.strip()
                address_line_1 = address_text.split("\n")[1]
                address_city_zip = address_text.split("\n")[-1]
            address_city, address_state_zip = address_city_zip.replace(
                "\n", ""
            ).split(", ")
            address_state, address_zip_code = (
                address_state_zip.split(" ")
                if len(address_state_zip.split(" ")) == 2
                else ("", "")
            )
            case_dict["address_city"] = address_city.strip()
            case_dict["address_line_1"] = address_line_1.strip()
            case_dict["address_zip"] = address_zip_code.strip()
            case_dict["address_state"] = address_state.strip()
            case_dict["county"] = address_city
        except Exception as e:
            console.log(f"Error in extracting address: {e}")
            case_dict["address_city"] = "N/A"
            case_dict["address_line_1"] = "N/A"
            case_dict["address_zip"] = "N/A"
            case_dict["address_state"] = "N/A"
            case_dict["county"] = ""
            case_dict["address_error"] = True

        try:
            charges_text = record.split("Charges:")[-1].strip()
            case_dict["charges"] = [
                {"description": item} for item in charges_text.split("\n")
            ]
        except Exception as e:
            console.log(f"Error in extracting charges: {e}")
            console.log(f"charges_text: {charges_text}")
            case_dict["charges"] = [{"description": "N/A"}]
            case_dict["charges_error"] = True

        county = case_dict["county"]
        case_dict["court_id"] = self.get_court_id(county)
        case_dict["court_code"] = case_dict["court_id"]
        case_dict["status"] = "new"
        case_dict["case_date"] = case_dict["filing_date"]
        case_dict["charges_description"] = " ".join(
            [item["description"] for item in case_dict["charges"]]
        )
        case_dict["address"] = case_dict["address_line_1"]
        case_dict["city"] = case_dict["address_city"]
        case_dict["zip_code"] = case_dict["address_zip"]
        case_dict["source"] = "md_general"
        case_dict["state"] = "MD"
        case_dict["record"] = record

        return case_dict

    def increase_date_by_one_day(self, date_str):
        """Increase the given date string by one day."""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        new_date_obj = date_obj + timedelta(days=1)
        return new_date_obj.strftime("%Y-%m-%d")

    def get_full_path(self, filename):
        # get the directory of the current script
        dir_path = os.path.join(settings.DATA_PATH, "md_general")

        # create the directory if it doesn't exist
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # full path of the file
        full_path = os.path.join(
            settings.DATA_PATH, "md_general", f"{filename}.pdf"
        )
        return full_path

    def extract_pdf(self, input_pdf):
        """
        extract PDF and return list of dict
        """
        full_path = self.get_full_path(input_pdf)
        # Parse the PDF content
        try:
            raw = parser.from_file(full_path)
        except Exception as err:
            console.log(f"Failed to Load PDF\t{input_pdf}\t{err}")
            return {}
        # read content
        text = raw["content"]
        if not text:
            console.log(f"No Content Found:\t{text}")
            return False
        # strip extra spaces
        text = text.strip()

        # split by pages using regex
        page_pattern = r"Run Date: \d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2} [AP]M"
        pages = re.split(page_pattern, text)
        if not pages:
            console.log(f"No Page Found:\t{len(text)}")
            return False
        # ignore last item
        pages = pages[:-1]

        master_list = []
        for i, page in enumerate(pages):
            try:
                page = page.split("Case Number Style Case Type File Date")[
                    -1
                ].strip()

                # extract records on each page
                records = self.extract_records(page)

                records = [item for item in records[1].split("$$$")]

                if not records:
                    console.log(f"No records Found:\t{len(records)}")
                    break
            except Exception as e:
                continue

            for j, record in enumerate(records):
                data = self.extract_data_points(record)
                if not data:
                    console.log(f"Record Extraction Failed:\t{record}")
                    continue
                master_list.append(data)
        df = pd.DataFrame(master_list)
        df.to_csv(f"md_general_{input_pdf}.csv", index=False)
        return master_list

    def scrape_cases_for_scraping_date(self, scraping_date):
        url = f"https://www.mdcourts.gov/data/case/file{scraping_date}.pdf"
        console.log(f"Downloading PDF file for {scraping_date}...")
        console.log(f"URL: {url}")
        filename = f"file{scraping_date}.pdf"

        # create full file path
        full_path = self.get_full_path(filename)

        try:
            response = requests.get(url)

            if response.status_code == 200:
                with open(full_path, "wb") as f:
                    f.write(response.content)
                console.log(f"PDF file has been downloaded at: {full_path}")

                input_pdf = f"file{scraping_date}.pdf"
                case_dicts = self.extract_pdf(input_pdf)
                console.log(
                    "Successfully extracted case_list for  scraping_date",
                    scraping_date,
                )
                return case_dicts
            else:
                console.log(
                    f"Failed to download file, status code: {response.status_code}"
                )

                # Check if the file exists
                if os.path.exists(full_path):
                    input_pdf = f"file{scraping_date}.pdf"

        except requests.RequestException as e:
            console.log(e)

    async def scrape(self):
        """Main scraping function to handle the entire scraping process."""
        last_scraping_date = self.state.get("last_filing_date", "2024-07-20")
        scraping_date = last_scraping_date
        not_found_count = 0

        while True:
            try:
                if not_found_count > 10:
                    console.log("Too many dates not found. Ending the search.")
                    break
                last_scraping_date = self.increase_date_by_one_day(
                    last_scraping_date
                )
                scraping_date = last_scraping_date

                self.state["last_scraping_date"] = last_scraping_date
                # self.update_state()

                case_dicts = self.scrape_cases_for_scraping_date(scraping_date)
                if case_dicts is None:
                    console.log(f" {scraping_date} not found. Skipping ...")
                    not_found_count += 1
                    continue

                not_found_count = 0

                for case_dict in case_dicts:
                    console.log("case_dict", case_dict)
                    case_id = case_dict["case_id"]
                    if self.check_if_exists(case_id):
                        console.log(
                            f"Case {case_id} already exists. Skipping..."
                        )
                        continue

                    console.log(f"Inserting case {case_id}...")
                    self.insert_case(case_dict)
                    console.log(f"Inserted case for {case_id})")
                    self.insert_lead(case_dict)
                    console.log(f"Inserted lead for {case_id}")

            except Exception as e:
                console.log(f"Failed to while scraping {scraping_date} - {e}")
                continue


if __name__ == "__main__":
    scraper = MDScraper()
    asyncio.run(scraper.scrape())
