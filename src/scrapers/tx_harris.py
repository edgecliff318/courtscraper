from datetime import date, datetime, time
from tempfile import NamedTemporaryFile

import pandas as pd
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress

from src.scrapers.base.scraper_base import ScraperBase

console = Console()


class TXHarrisCountyScraper(ScraperBase):
    field_mapping = {
        "Case Number": "case_id",
        "JP Court ID ": "court_id",
        "Citation Number ": "ticket",
        "Filed Date": "filing_date",
        "Offense Code": "charges",
        "Offense Description ": "description",
        "Statutory Cite 1 ": "case_desc",
        "Statutory Cite 2 ": "related_cases",  # Assuming related laws might imply related cases
        "Arresting Agency Code ": "court_code",  # Closest match; may not be perfect
        "Arresting Agency Name ": "court_desc",
        "Officer Code": "source",  # Assuming the officer's code is a source identifier
        "Officer Name": "prosecuting_atty",  # Close approximation; officer acting as complainant
        "Plea Code": "plea_andpayind",
        "Plea Date ": "plea_date",
        "Disposition Code ": "status",
        "Disposition Date ": "case_status",
        "Judgment Date": "case_date",
        "Def First Name ": "first_name",
        "Def Middle Name": "middle_name",
        "Def Last Name": "last_name",
        "Def Suffix ": "suffix",  # No direct match; added as 'suffix'
        "Def Home Add Line 1": "address_line_1",
        # "Def Home Add Line 2": "address_seq_no",  # Approximation; sequence no. may refer to multi-line addresses REMOVED;
        "Def Home Add Line 2": "address_line_2",
        "Def Home Add City": "address_city",
        "Def Home Add State ": "address_state_code",
        "Def Home Add ZIP 1 ": "address_zip",
        # 'Def Home Add ZIP 2 ': Not directly mapped; possibly combine with 'Def Home Add ZIP 1 ' if needed
        "Def Work Add Line 1": "formatted_party_address",  # Assuming work address is a formatted party address
        # Remaining work address fields are not directly mapped due to lack of direct correspondence
        "Def Date of Birth": "birth_date",
        "Def SPN Number": "pidm",  # Assuming SPN number can serve as a unique identifier akin to PIDM
        "Def SPN Pointer": "custom",  # No direct match; 'custom' for miscellaneous data
        "Def Height Feet": "height_feet",  # No direct match; added as 'height'
        "Def Height Inches": "height_inches",  # Combine with 'Def Height Feet' for full height in one field
        "Def Weight": "weight",  # No direct match; added as 'weight'
        "Def Gender ": "gender",
        "Def Race": "race",  # No direct match; added as 'race'
        "Total Fines Assessed ": "fine",
        "Total Fines Due": "balance_due",  # Assuming closest match for dues
        # The fields related to costs, payments, bond details, and hearing details are not directly mapped due to lack of direct correspondence or because they are overly specific without a clear counterpart.
        "Next Hearing Date": "court_date",
        "Next Hearing Time": "court_time",
        # 'Next Hearing Desc', 'Last Open Warr Type', 'Last Open Warr Date': Not directly mapped due to lack of clear counterparts
    }

    def get_courts(self):
        self.search_url = (
            "https://jpwebsite.harriscountytx.gov/PublicExtracts/search.jsp"
        )
        res = requests.get(url=self.search_url)
        if res.status_code != 200:
            raise Exception("Failed to get search page")
        parser = BeautifulSoup(res.text, "html.parser")
        courts = parser.find("select", id="court").find_all("option")
        return [
            {"court_id": str(court["value"]), "name": court.text.strip()}
            for court in courts
        ]

    def scraper_single_court(self, court_id, start_date, end_date):
        params = {
            "extractCaseType": "CR",
            "extract": "1",
            "court": court_id,
            "casetype": "CRCIT,CRCOM",
            "format": "csv",
            "fdate": start_date,
            "tdate": end_date,
        }

        response = requests.get(
            url=self.url,
            params=params,
        )

        with NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as f:
            f.write(response.text)
            filepath = f.name
            cases_dicts = self.extract_cases(filepath)
            console.log(f"Extracted {len(cases_dicts)} cases")

            # with progress
            with Progress() as progress:
                task = progress.add_task(
                    "[red]Inserting cases...", total=len(cases_dicts)
                )
                for case_dict in cases_dicts:
                    case_id = case_dict.get("case_id")
                    if self.check_if_exists(case_id):
                        console.log(
                            f"Case {case_id} already exists. Skipping..."
                        )
                        progress.update(task, advance=1)
                        continue
                    self.insert_case(case_dict)
                    self.insert_lead(case_dict)

                    progress.update(task, advance=1)

    def extract_cases(self, filepath):
        try:
            df = pd.read_csv(filepath, skip_blank_lines=True)
            if df.empty:
                return []
        except pd.errors.EmptyDataError:
            return []
        except pd.errors.ParserError:
            return []

        df = df[list(self.field_mapping.keys())].rename(
            columns=self.field_mapping
        )

        df["court_date_parsed"] = pd.to_datetime(
            df["court_date"], format='%m/%d/%Y"%H:%M"'
        )

        df["court_date"] = df["court_date_parsed"].dt.date
        df["court_time"] = df["court_date_parsed"].dt.time

        df["height"] = (
            df["height_feet"].astype(str)
            + "'"
            + df["height_inches"].astype(str)
        )

        df["court_code"] = "TX_HARRIS"
        df["source"] = "tx_harris"
        df["city"] = df["address_city"]
        df["state"] = "TX"
        df["zip_code"] = df["address_zip"].astype(str)
        df["address_zip"] = df["address_zip"].astype(str)
        df["case_id"] = df["case_id"].astype(str)
        df["county"] = "Harris"
        df["case_date"] = df["filing_date"]
        df["case_date"] = pd.to_datetime(df["case_date"], format="%m/%d/%Y")
        df["charges_description"] = df["description"]
        df["case_desc"] = str(df["case_desc"])
        df["source"] = "tx_harris"

        cases_dicts = df.to_dict(orient="records")
        cases_dicts = [
            {k: (None if pd.isna(v) else v) for k, v in record.items()}
            for record in cases_dicts
        ]
        for cases_dict in cases_dicts:
            cases_dict["related_cases"] = (
                [cases_dict["related_cases"]]
                if isinstance(cases_dict["related_cases"], str)
                else cases_dict["related_cases"]
            )

            cases_dict["prosecuting_atty"] = (
                None  # I set this to None for now, not sure if this is True/False for default values
            )
            cases_dict["fine"] = {
                "default_courtcost": 0,
                "total_amount": cases_dict["fine"],
                "total_vbfineamount": cases_dict["fine"],
            }
            cases_dict["ticket"] = {}  # Push this as empty dict
            cases_dict["court_date"] = (
                datetime.combine(cases_dict["court_date"], time())
                if cases_dict["court_date"]
                else None
            )
            cases_dict["court_time"] = str(cases_dict["court_time"])
            cases_dict["charges"] = [
                {
                    "description": cases_dict["charges"],
                }
            ]

        return cases_dicts

    def scrape(self, search_parameters):
        start_date = search_parameters.get("start_date")
        end_date = search_parameters.get("end_date")

        if not start_date:
            start_date = date.today().strftime("%m/%d/%Y")
        if not end_date:
            end_date = date.today().strftime("%m/%d/%Y")

        self.url = "https://jpwebsite.harriscountytx.gov/PublicExtracts/GetExtractData"

        # Get the list of courts
        courts_list = self.get_courts()

        # Loop for each court in the list of courts
        for court in courts_list:
            court_id = court.get("court_id")
            self.scraper_single_court(court_id, start_date, end_date)


if __name__ == "__main__":
    txscraper = TXHarrisCountyScraper()
    txscraper.scrape({"start_date": "07/21/2024", "end_date": "07/21/2024"})
