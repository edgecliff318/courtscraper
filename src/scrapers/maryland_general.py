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


def is_valid_date(date_string):
    """Checks if the date string matches the format YYYY-MM-DD.

    Args:
        date_string: The date string to check.

    Returns:
        True if the date string matches the format, False otherwise.
    """
    date_regex = r"^\d{4}-\d{2}-\d{2}$"
    return bool(re.match(date_regex, date_string))


def construct_pdf_path(input_pdf: str):
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


def read_pdf(input_pdf: str) -> str:
    # Parse the PDF content
    try:
        raw = parser.from_file(input_pdf)
    except FileNotFoundError:
        print(f"File not found: {input_pdf}")
        return ""
    except Exception as err:
        print(f"Failed to Load PDF\t{input_pdf}\t{err}")
        return ""

    # read content
    text = raw.get("content")  # type: ignore

    if not text:
        print(f"No Content Found in PDF:\t{text}")
        return ""

    # strip extra spaces
    text = text.strip()

    # replace trash values like page number etc
    replace_pattern_list = [
        "Run Date: .*",
        ".*\n\nCase Number .*",
        "\n\n\nAOC - Cases Filed Report\n.*\n.*\n.*",
        "Cases Filed Report",
    ]
    for replace_pattern in replace_pattern_list:
        text = re.sub(replace_pattern, "", text)

    return text


def get_cases(text: str) -> list:
    case_pattern = r"^\n([A-Z\-0-9]{3,}) [\n\D]*\d{1,2}/\d{2}/\d{4}"
    matches = re.finditer(case_pattern, text, flags=re.MULTILINE)
    try:
        first_match = next(matches)
    except Exception:
        print("Match Not Found.")
        return []

    cases = []
    temp_start = first_match.start()
    for i, match in enumerate(matches):
        print(f"Iteration:\t{i}")
        end_index = match.start()
        cases.append(text[temp_start:end_index])
        temp_start = match.start()
    cases.append(text[end_index : match.end()])
    print(f"Total Cases Fetched:\t{len(cases)}")
    return cases


def extract_data_points(case: str) -> dict:
    case_dict = {}

    # fetch case id
    case_id, case = case.strip().split(" ", 1)

    # there are cases with no charges
    if "Charges:" in case:
        case, case_charges = case.split("Charges:")

        # extract charges
        case_dict["charges"] = [
            {"description": item} for item in case_charges.strip().split("\n")
        ]
    else:
        case_dict["charges"] = []

    # there are no Defendant Address mentioned
    if "Defendant Address:" in case:
        # fetch defendant details
        case, case_def = case.strip().split("Defendant Address:")

        # fetch name / address
        name_details, address_details = case_def.strip().split("\n", 1)

        # fetch name
        last_name, name_details = name_details.strip().split(",", 1)
        first_name, middle_name = (
            name_details.strip().split(" ", 1)
            if len(name_details.strip().split(" ", 1)) > 1
            else [name_details.strip().split(" ", 1)[0], ""]
        )
        if not first_name:
            # no first name means bad case
            return {}

        # fetch address line
        address_line_1, address_details = address_details.strip().split("\n", 1)
        # fetch address city
        address_city, address_details = address_details.strip().split(",", 1)
        # fetch address state and zip code
        address_state, address_zip = address_details.strip().split(" ", 1)
    else:
        # address and name not found can't collect data
        return {}

    # fetch filing date
    filing_date_match = re.search(
        r"(\d{1,2}/\d{2}/\d{4})", case.strip(), flags=re.MULTILINE
    )

    if filing_date_match:
        filing_date = filing_date_match.group(1)
    else:
        filing_date = ""

    case_dict["case_id"] = case_id

    case_dict["first_name"] = first_name
    case_dict["middle_name"] = middle_name
    case_dict["last_name"] = last_name

    case_dict["address_line_1"] = address_line_1
    case_dict["address_city"] = address_city
    case_dict["county"] = address_city
    case_dict["address_zip"] = address_zip
    case_dict["address_state"] = address_state
    case_dict["filing_date"] = (
        datetime.strptime(filing_date, "%m/%d/%Y") if filing_date else filing_date
    )
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


def extract_pdf(input_pdf: str) -> list:
    """extract PDF and return list of dict

    Args:
        input_pdf (str): pdf file path

    Returns:
        list: extracted list of dictionaries
    """

    text = read_pdf(input_pdf)
    if not text:
        exit()

    cases = get_cases(text)

    total_cases: list[dict] = []
    for case_text in cases:
        try:
            data = extract_data_points(case_text.strip())
            total_cases.append(data) if data else ""
        except Exception:
            pass

    return total_cases


class MDGeneralScraper(ScraperBase):
    def __init__(self):
        super().__init__()
        self.courts = {}
        self.browser = None
        self.page = None
        self.url = "https://www.mdcourts.gov/mdec/publiccases"

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

    def increase_date_by_one_day(self, date_str):
        """Increase the given date string by one day."""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        new_date_obj = date_obj + timedelta(days=1)
        return new_date_obj.strftime("%Y-%m-%d")

    def scrape_cases_for_scraping_date(self, scraping_date):
        if is_valid_date(scraping_date):
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
            full_pdf_path = construct_pdf_path(file_name)

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
                case_dicts = extract_pdf(full_pdf_path)
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
        """Main scraping function to handle the entire scraping process."""
        last_scraping_date = self.state.get("last_filing_date", "2024-08-02")
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

                case_dicts = self.scrape_cases_for_scraping_date(scraping_date)
                if case_dicts is None:
                    console.log(f" {scraping_date} not found. Skipping ...")
                    not_found_count += 1
                    continue

                not_found_count = 0

                for case_dict in case_dicts:
                    print("case_dict", case_dict)
                    case_id = case_dict["case_id"]
                    try:
                        case_dict["court_id"] = self.get_court_id(case_dict["county"])
                        case_dict["court_code"] = case_dict["court_id"]
                    except:
                        continue
                    if self.check_if_exists(case_id):
                        console.log(f"Case {case_id} already exists. Skipping...")
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
    MDGeneralScraper = MDGeneralScraper()
    asyncio.run(MDGeneralScraper.scrape())