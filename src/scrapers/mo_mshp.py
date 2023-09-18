import logging
from time import sleep
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import track

console = Console()

logger = logging.getLogger(__name__)


class MOHighwayPatrol(object):
    def __init__(self) -> None:
        self.url = "https://www.mshp.dps.missouri.gov/HP71/search.jsp"
        self.base_url = "https://www.mshp.dps.missouri.gov/"

    def get_single_report(self, url):
        report_url = urljoin(self.base_url, url)

        response = requests.get(report_url)

        # Get the two tables
        soup = BeautifulSoup(response.text, "html.parser")

        all_reports = {}

        for table in soup.find_all("table", {"class": "accidentOutput"}):
            table_name = table.find("caption").text.strip()
            table_name = table_name.replace(" ", "_").lower()

            reports = self.extract_table(table)

            all_reports[table_name] = reports

        return all_reports

    def extract_table(self, table, get_link=False):
        rows = table.find_all("tr")

        # Transform the table into a list of dicts
        reports = []
        headers = []

        for row in rows:
            # If the row is a header, get the column names
            if row.find("th"):
                headers = row.find_all("th")
                headers = [header.text.strip() for header in headers]
                headers = [
                    header.replace(" ", "_").lower() for header in headers
                ]
                continue

            cells = row.find_all("td")
            report = {}
            for column, cell in zip(headers, cells):
                if get_link and cell.find("a"):
                    report["link"] = cell.find("a")["href"]

                report[column] = cell.text.strip()
            reports.append(report)

        return reports

    def get_latest_reports(self, cases_filter=None):
        response = requests.get(self.url)

        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table", {"class": "accidentOutput"})

        reports = self.extract_table(table, get_link=True)
        reports_output = []

        for report in track(reports):
            report["case_id"] = self.generate_case_id(report)
            if cases_filter and report["case_id"] not in [
                c.case_id for c in cases_filter
            ]:
                continue
            data = self.get_single_report(report["link"])
            sleep(1)
            persona_information = data["person_information"][0]
            report.update(persona_information)
            reports_output.append(report)

        return reports_output

    def generate_case_id(self, report):
        output = f"{report['name']}_{report['age']}_{report['arrest_date']}"
        # Remove the whitespace and replace with _
        output = output.replace(" ", "_").replace(",", "_").replace("/", "_")
        return output

    def get_cases(self, cases_filter=None):
        reports = self.get_latest_reports(cases_filter=cases_filter)
        cases = []
        for report in reports:
            case_id = report["case_id"]
            name = report["name"]
            # Split to get the first and last name
            first_name, last_name = name.split(", ", 1)
            try:
                city, state = report.get("person_city/state", ",").split(",")
            except Exception:
                city = report.get("person_city/state")
                state = "MO"
                logger.error(
                    f"Failed to split city and state for case {case_id} - {report.get('person_city/state')}"
                )

            # Getting the case info
            case_info = {
                "case_id": case_id,
                "case_type": "mo_mshp",
                "court_id": "temp",  # TODO: Check with Shawn
                "court_code": "temp",
                "case_date": report.get("arrest_date"),
                "source": "mo_mshp",
                "formatted_party_name": name,
                "first_name": first_name,
                "last_name": last_name,
                "age": report.get("age"),
                "charges_description": report.get("charge"),
                "arrest_time": report.get("arrest_time"),
                "arrest_date": report.get("arrest_date"),
                "gender": report.get("person_gender"),
                "where_held": report.get("where_held"),
                "release_info": report.get("release_info"),
                "address_city": city,
                "address_state_code": state,
            }
            logger.info(f"Succeeded to get details for case " f"{case_id}")
            console.print(f"Succeeded to get details for case " f"{case_id}")
            cases.append(case_info)
        return cases


if __name__ == "__main__":
    scraper = MOHighwayPatrol()
    scraper.get_latest_reports()
