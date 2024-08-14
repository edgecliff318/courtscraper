"""Scraper for Oklahoma Court"""

import requests
import os, re
import pandas as pd

from models.cases import Case
from models.leads import Lead
from src.scrapers.base.scraper_base import ScraperBase

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile
from rich.console import Console
from rich.console import Console
from rich.progress import Progress

from twocaptcha import TwoCaptcha
TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')

console = Console()

class OklahomaScraper(ScraperBase):
    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

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
   
    def increase_date_by_one_day(self, date_str):
        """Increase the given date string by one day."""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        new_date_obj = date_obj + timedelta(days=1)
        return new_date_obj.strftime("%Y-%m-%d")

    def get_courts(self):
        url = "https://www.oscn.net/dockets/Search.aspx"
        res= requests.get(url, headers=self.headers)
        soup = BeautifulSoup(res.text, "html.parser")
        dblist_element = soup.select_one("#dblist")
            
        if dblist_element is not None:
            courts_options = dblist_element.select("option")[1:]
            courts = [
                {
                    "court_id": court.get("value"),
                    "court_code": court.get("value"),
                    "court_desc": court.text
                }
                for court in courts_options
            ]
            return courts

    def get_cases(self, court_id, filed_date):
        base_url = "https://www.oscn.net/dockets/Results.aspx"

        params = {
            "db": court_id,
            "apct": "45",
            "dcct": "18",
            "FiledDateL": filed_date,
            "FiledDateH": filed_date,
        }

        response = requests.get(base_url, headers=self.headers, params=params)
        soup = BeautifulSoup(response.text, "html.parser")
        cases_rows = soup.select("tr.resultTableRow")

        return cases_rows

    def get_case_detail(self, case_row):

        id_field = case_row.select_one(".result_casenumber")
        description_field = case_row.select_one(".result_shortstyle")
        filing_date_field = case_row.select_one(".result_datefiled")
        case_link_field = id_field.select_one("a") if id_field else None
        
        case_id = id_field.text if id_field else None
        description = description_field.text if description_field else None
        filing_date = filing_date_field.text if filing_date_field else None
        filing_date = datetime.strptime(filing_date, "%m/%d/%Y") if filing_date else None
        case_link = f'https://www.oscn.net/dockets/{case_link_field.get("href")}' if case_link_field else None

        case_dict = {
            "case_id": case_id,
            "description": description,
            "filing_date": filing_date,
            "case_date": filing_date
        }
        if not case_link:
            return case_dict
        
        res = requests.get(case_link, headers=self.headers)
        soup = BeautifulSoup(res.text, "html.parser")

        charges = self.get_charge_info(soup)
        parties, defendant_info = self.get_party_info(soup)

        case_dict = {
            **case_dict,
            **defendant_info,
            "charges": charges,
            "parties": parties
        }

        return case_dict

    def get_party_info(self, soup):
        party_header = soup.select_one("h2.section.party")
        party_p = party_header.find_next("p") # type: ignore
        segments = []
        current_segment_content = []
        for element in party_p.contents: # type: ignore
            if element.name == 'br': # type: ignore
                if current_segment_content:
                    segments.append(current_segment_content)
                    current_segment_content = []
            else:
                current_segment_content.append(element)

        # If anything is left after the last <br>
        if current_segment_content:
            segments.append(current_segment_content)

        parties = []
        for segment in segments:
            if len(segment) < 2:
                continue
            role = segment[1].text.replace(',', '').strip().lower()
            name = segment[0].text.strip()
            parties.append({"role": role, "name": name})

        link = f"https://www.oscn.net/dockets/{segments[0][0].get('href')}"
        res = requests.get(link, headers=self.headers)
        
        birth_date = ""
        try:
            birth_date = BeautifulSoup(res.text, "html.parser").select_one("table.partytable.personal").find("tbody").find_all("td") # type: ignore
            birth_date = birth_date[2].text.strip() if len(birth_date) > 3 else None # type: ignore
        except Exception as e:
            console.log(f"Birth Date Error: {e}")
        
        address_line_1 = ""
        try:
            address_line_1 = BeautifulSoup(res.text, "html.parser").select_one("table.partytable.addresses").find("tbody").find_all("td") # type: ignore
            address_line_1 = address_line_1[3].text.strip() if len(address_line_1) > 4 else None # type: ignore
        except Exception as e:
            console.log(f"Address Line 1 Error: {e}")

        first_name, middle_name, last_name = "", "", ""
        try:
            first_name, middle_name, last_name = self.split_full_name(parties[0]["name"]) # type: ignore 
        except Exception as e:
            console.log(f"Name Error: {e}")

        return parties, {
            "birth_date": birth_date,
            "address_line_1": address_line_1,
            "address": address_line_1,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name
        }
    
    def get_charge_info(self, soup):
        charge_header = soup.select_one("h2.section.counts")
        charges = []
        if charge_header:
            for sibling in charge_header.find_next_siblings():
                # If the sibling is a p tag, append it to the p_tags list
                if sibling.name == 'p':
                    charges.append({
                        "description": sibling.text.strip()
                    })
                # If the sibling is an h2 tag, stop searching
                elif sibling.name == 'h2':
                    break
        return charges
    
    def scrape(self):
        """Main scraping function to handle the entire scraping process."""
        last_filing_date = self.state.get("last_filing_date", "2024-07-10")
        filing_date = last_filing_date
        not_found_count = 0

        while True:
            try:
                if not_found_count > 10:
                    console.log(
                        "Too many filing dates not found. Ending the search."
                    )
                    break

                console.log("filing_date: ", filing_date)
                courts = self.get_courts()

                if courts is None:
                    console.log(
                        f"Courts not found. Skipping ..."
                    )
                    not_found_count += 1
                    continue
                
                for court in courts:
                    court_id = court.get("court_id")      
                    court_code = court.get("court_code")              
                    court_desc = court.get("court_desc")

                    cases_rows = self.get_cases(court_id, filing_date)
                    if not cases_rows:
                        console.log(
                            f"Case not found. Skipping ..."
                        )
                        not_found_count += 1
                        continue

                    not_found_count = 0
                
                    console.log(f"Found {len(cases_rows)} cases for {court_desc} on {filing_date}")
                    
                    for case_row in cases_rows:
                        case_dict = self.get_case_detail(case_row)
                        case_id = case_dict["case_id"]
                        console.log("case_id: ", case_id)
                        if self.check_if_exists(case_id):
                            console.log(
                                f"Case {case_id} already exists. Skipping..."
                            )
                            continue

                        case_dict = {
                            **case_dict,
                            "court_id": court_id,
                            "court_code": court_code,
                            "court_desc": court_desc,
                            "status": "new",
                            "state": "OK",

                        }
                        console.log("case_dict", case_dict)
                        # Check against the data model char
                        console.log(f"Inserting case for {case_id}...")
                        self.insert_case(case_dict)
                        console.log(f"Inserting lead for {case_id})")
                        self.insert_lead(case_dict)

                filing_date = self.increase_date_by_one_day(filing_date)

            except Exception as e:
                console.log(f"Failed to insert case - {e}")
                continue