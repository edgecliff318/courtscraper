from time import sleep
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from rich.progress import track


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

    def get_latest_reports(self):
        response = requests.get(self.url)

        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table", {"class": "accidentOutput"})

        reports = self.extract_table(table, get_link=True)

        for report in track(reports):
            data = self.get_single_report(report["link"])
            sleep(2)
            persona_information = data["person_information"][0]
            report.update(persona_information)

        return reports


if __name__ == "__main__":
    scraper = MOHighwayPatrol()
    scraper.get_latest_reports()
