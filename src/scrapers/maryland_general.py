"""Scraper for Maryland General Court"""

import asyncio
import os
import re
from datetime import datetime, timedelta

import requests
from rich.console import Console
from tika import parser

from src.scrapers.base.scraper_base import ScraperBase

# Configure logging
console = Console()


class MDGeneralScraper(ScraperBase):
    def __init__(self):
        super().__init__()
        self.courts = {}
        self.browser = None
        self.page = None
        self.url = "https://www.mdcourts.gov/mdec/publiccases"

    def is_valid_number(self, x):
        return any(char.isdigit() for char in x) and any(char.isalpha() for char in x)

    def construct_pdf_path(self, input_pdf: str):
        """construct_pdf_path will construct complete file path from file name

        Args:
            input_pdf (str): file name

        Returns:
            str: full file path
        """
        # get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # create full file path
        full_path = os.path.join(script_dir, input_pdf)
        return full_path

    def is_valid_date(self, date_string):
        """Checks if the date string matches the format YYYY-MM-DD.

        Args:
            date_string: The date string to check.

        Returns:
            True if the date string matches the format, False otherwise.
        """
        date_regex = r"^\d{4}-\d{2}-\d{2}$"
        return bool(re.match(date_regex, date_string))

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
                        next_record = (
                            f"{number}|||{page[page.index(number) + len(number) :]}"
                        )

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
        try:
            case_id_name_splits = citation_splits[0].split("|||")
            case_dict["case_id"] = case_id_name_splits[0].strip()
            name = case_id_name_splits[1].strip()
            first_name, middle_name, last_name = self.split_full_name(name)
            case_dict["first_name"] = first_name
            case_dict["middle_name"] = middle_name
            case_dict["last_name"] = last_name
        except:
            case_dict["first_name"] = "N/A"
            case_dict["middle_name"] = "N/A"
            case_dict["last_name"] = "N/A"

        try:
            case_type_n__filling_date = (
                citation_splits[1].strip(" - ").split("\n", 1)[0]
            )
            date_match = re.search(r"(\d{2}/\d{2}/\d{4})", case_type_n__filling_date)
            filing_date = date_match.group(1).strip()
            case_dict["filing_date"] = self.to_datetime(filing_date)
        except:
            case_dict["filing_date"] = None

        try:
            case_dict["case_type"] = case_type_n__filling_date[
                : date_match.start()
            ].strip()
        except:
            case_dict["case_type"] = "N/A"

        try:
            # complete address
            complete_address_n_charges = (
                citation_splits[1]
                .strip(" - ")
                .split("\n", 1)[1]
                .split("\n\n\n\n")[0]
                .strip("Defendant Address:")
                .strip()
            )
            address_lines = complete_address_n_charges.split("Charges:")[0].split("\n")
            address_lines = [item for item in address_lines if item]

            address_line_1 = address_lines[1].strip() if len(address_lines) > 1 else ""

            address_city, address_state_zip = (
                address_lines[2].split(", ") if len(address_lines) > 2 else ("", "")
            )
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
            case_dict["address_city"] = "N/A"
            case_dict["address_line_1"] = "N/A"
            case_dict["address_zip"] = "N/A"
            case_dict["address_state"] = "N/A"
            case_dict["county"] = ""

        try:
            charges_text = complete_address_n_charges.split("Charges:")[-1].strip()
            case_dict["charges"] = [
                {"description": item for item in charges_text.split("\n")}
            ]
        except Exception as e:
            case_dict["charges"] = [{"description": "N/A"}]

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
        case_dict["source"] = "Maryland General"

        return case_dict

    def increase_date_by_one_day(self, date_str):
        """Increase the given date string by one day."""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        new_date_obj = date_obj + timedelta(days=1)
        return new_date_obj.strftime("%Y-%m-%d")

    def extract_pdf(self, input_pdf: str) -> list:
        """extract PDF and return list of dict

        Args:
            input_pdf (str): pdf file path

        Returns:
            list: extracted list of dictionaries
        """
        # Parse the PDF content
        try:
            raw = parser.from_file(input_pdf)
        except FileNotFoundError:
            print(f"File not found: {input_pdf}")
            return []
        except Exception as err:
            print(f"Failed to Load PDF\t{input_pdf}\t{err}")
            return []

        # read content
        text = raw.get("content")  # type: ignore

        if not text:
            print(f"No Content Found in PDF:\t{text}")
            return []

        # strip extra spaces
        text = text.strip()

        # split by pages using regex
        page_pattern = r"Run Date: \d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2} [AP]M"
        pages = re.split(page_pattern, text)
        if not pages:
            print(f"No Page Found:\t{len(text)}")
            return []
        # ignore last item
        pages = pages[:-1]

        master_list = []
        for i, page in enumerate(pages):
            try:
                page = page.split("Case Number Style Case Type File Date")[-1].strip()

                # extract records on each page
                records = self.extract_records(page)

                records = [item for item in records[1].split("$$$")]

                if not records:
                    print(f"No records Found:\t{len(records)}")
                    break
            except Exception:
                continue

            for j, record in enumerate(records):
                data = self.extract_data_points(record)
                if not data:
                    print(f"Record Extraction Failed:\t{record}")
                    continue
                master_list.append(data)

        return master_list

    def scrape_cases_for_scraping_date(self, scraping_date):
        if self.is_valid_date(scraping_date):
            # construct pdf url from date
            url = f"https://www.mdcourts.gov/data/case/file{scraping_date}.pdf"
            print(url)
        else:
            print(f"Invalid Input Date:\t{scraping_date}")
            return []
        # make request to pdf url
        try:
            response = requests.get(url)
        except requests.RequestException as err:
            print(f"Request Exception Occurred At PDF Url:\t{url}\t{err}")
            return []
        except Exception as err:
            print(f"Exception Occurred At PDF Url:\t{url}\t{err}")
            return []

        if response.status_code == 200:
            # construct file name on successful request
            file_name = f"file{scraping_date}.pdf"
            # construct full file path
            full_pdf_path = self.construct_pdf_path(file_name)

            # make directory if not exists
            os.makedirs(os.path.dirname(full_pdf_path), exist_ok=True)

            # save pdf
            try:
                with open(full_pdf_path, "wb") as f:
                    f.write(response.content)
                print(f"PDF file has been downloaded at: {full_pdf_path}")
            except OSError as err:
                print(f"Error writing PDF to file: {err}")
            except Exception as err:
                print(f"Unexpected error: {err}")

            if os.path.exists(full_pdf_path):
                # file exists
                case_dicts = self.extract_pdf(full_pdf_path)
                print(
                    f"Successfully extracted case_list for  scraping_date:\t{scraping_date}"
                )
            else:
                # file doesn't exist
                case_dicts = []
        elif response.status_code == 404:
            # Status code 404 means file not exist on the url
            print(f"404 File Not Found. Url: {url}")
            case_dicts = []
        else:
            # request not successful. Status code not 200
            print(f"Failed to download file, status code: {response.status_code}")
            case_dicts = []
        return case_dicts

    async def scrape(self):
        """ Main scraping function to handle the entire scraping process. """
        last_scraping_date = self.state.get("last_filing_date", "2024-07-16")
        scraping_date = last_scraping_date
        not_found_count = 0

        while True:
            try:
                if not_found_count > 10:
                    console.log("Too many dates not found. Ending the search.")
                    break
                last_scraping_date = self.increase_date_by_one_day(last_scraping_date)
                scraping_date = last_scraping_date

                self.state["last_scraping_date"] = last_scraping_date
                # self.update_state()

                case_dicts= self.scrape_cases_for_scraping_date(scraping_date)
                if case_dicts is None:
                    console.log(f" {scraping_date} not found. Skipping ...")
                    not_found_count += 1
                    continue
                                
                not_found_count = 0

                for case_dict in case_dicts:
                    print("case_dict", case_dict)
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
    mdgeneralscraper = MDGeneralScraper()
    asyncio.run(mdgeneralscraper.scrape())