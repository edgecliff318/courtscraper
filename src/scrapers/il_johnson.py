""" Scraper for Johnson Superior Court """
import json
import os.path
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from src.scrapers.base import (
    InitializedSession,
    NameNormalizer,
    ScraperBase,
    TextNormalizer,
)

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    + "/libraries"
)

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
)


class ScraperILJohnsonSuperior(ScraperBase):
    """IL Johnson Superior Court scraper"""

    BASE_URL = "https://www.judici.com"
    COURT_ID = "IL044015J"
    SEARCH_RESULT_PAGE_URL = "https://www.judici.com/courts/cases/case_search.jsp?court={}&sort=full_name&order=ASC&case_number=&litigant_name={}&charge_text=&offset={}"

    def scrape(self, search_parameters):
        """Entry point for lambda.

        Query should look like this:

        {
            "lastName": "Smith",
            "firstName": "R",
            "dob": "12/27/1978"
        }
        https://<endpoint>?queryStringParameters
        """
        last_name = search_parameters["lastName"]
        first_name = search_parameters["firstName"]
        dob = search_parameters["dob"]
        return self.search_in_johnson_il(first_name, last_name, dob)

    GLOBAL_SESSION = InitializedSession()

    def parse_table_row(self, row):
        """Get object from row of case detail using given row element

        This function returns an object.
        """
        key = ""
        obj = {}
        if row.has_key("class") and row["class"][0] == "case_level_4":
            return {}
        for cell in row.findAll("td"):
            if cell.has_key("class") and cell["class"][0] == "case_level_3":
                obj[key] = TextNormalizer(cell.text).normalized()
            else:
                key = TextNormalizer(cell.text).normalized()
        return obj

    def get_case_information(self, case_url):
        """Get case information of case detail using given url

        This function returns an object.
        """
        case_information = {}
        try:
            r = self.GLOBAL_SESSION.get(case_url)
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return case_information
        soup = BeautifulSoup(r.text, features="html.parser")
        table = soup.find("table")
        if table:
            rows = table.findAll("tr")
            information_key = ""
            object_key = []
            keys_for_object = [
                "Litigant Information",
                "Identification",
                "Address",
            ]
            keys_for_table = ["Hearings", "Other Litigants"]
            for row in rows:
                if row.has_key("class"):
                    cells = row.findAll("td")
                    if row["class"][0] == "case_level_1":
                        information_key = TextNormalizer(row.text).normalized()
                        object_key = []
                        continue
                    if (
                        information_key not in keys_for_table
                        and information_key not in keys_for_object
                    ):
                        if row.has_key("class"):
                            if row["class"][0] == "case_level_4":
                                case_information[information_key] = {}
                            elif row["class"][0] == "case_level_2":
                                if (
                                    len(
                                        row.findAll(
                                            "td", class_="case_level_3"
                                        )
                                    )
                                    == 0
                                ):
                                    keys_for_table.append(information_key)
                                else:
                                    keys_for_object.append(information_key)
                    if information_key == "":
                        if row["class"][0] == "case_level_2":
                            case_information = {
                                **case_information,
                                **(self.parse_table_row(row)),
                            }
                    elif information_key in keys_for_object:
                        if information_key not in case_information:
                            case_information[information_key] = {}
                        case_information[information_key] = {
                            **case_information[information_key],
                            **(self.parse_table_row(row)),
                        }
                    elif information_key in keys_for_table:
                        if information_key not in case_information:
                            case_information[information_key] = []
                        if row.has_key("class"):
                            if row["class"][0] == "case_level_4":
                                case_information[information_key] = []
                            elif row["class"][0] == "case_level_2":
                                for cell in row.findAll("td"):
                                    object_key.append(
                                        TextNormalizer(cell.text).normalized()
                                    )
                            elif row["class"][0] == "case_level_3":
                                cells = row.findAll("td")
                                obj = {}
                                for i in range(0, len(cells)):
                                    obj[object_key[i]] = TextNormalizer(
                                        cells[i].text
                                    ).normalized()
                                case_information[information_key].append(obj)

        return case_information

    def parse_information_table(self, table):
        """Parse information table and get array of object

        This function returns an array.
        """
        information = []
        rows = table.findAll("tr")
        keys = []
        for row in rows:
            if row.find("th"):
                for cell in row.findAll("th"):
                    keys.append(TextNormalizer(cell.text).normalized())
            else:
                cells = row.findAll("td")
                obj = {}
                if len(cells) == len(keys):
                    for i in range(0, len(cells)):
                        obj[keys[i]] = TextNormalizer(
                            cells[i].text
                        ).normalized()
                    information.append(obj)

        print(information)
        return information

    def get_case_detail_from_table(self, case_url):
        """Get case information of case detail using given url

        This function returns an object.
        """

        try:
            r = self.GLOBAL_SESSION.get(case_url)
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return []
        soup = BeautifulSoup(r.text, features="html.parser")
        table = soup.find("table")
        if table:
            return self.parse_information_table(table)

        return []

    def get_case_detail(self, case_url):
        """Get every information of case detail by parsing rendered HTML page

        This function returns an object.
        """
        return {
            "case_information": self.get_case_information(case_url),
            "case_dispositions": self.get_case_detail_from_table(
                case_url.replace("case_information", "case_dispositions")
            ),
            "case_history": self.get_case_detail_from_table(
                case_url.replace("case_information", "case_history")
            ),
            "case_payment_history": self.get_case_detail_from_table(
                case_url.replace("case_information", "case_payment_history")
            ),
            "case_fines_fees": self.get_case_detail_from_table(
                case_url.replace("case_information", "case_fines_fees")
            ),
        }

    def parse_search_results(self, soup, input_dob):
        """Parse rendered HTML page for search result and get matched cases using given firstName and lastName

        If test is set to parsed HTML, like what BeautifulSoup provides,
        the code will not attempt a lookup on the web site,
        but will instead use that HTML.

        This function returns an array.
        """
        cases = []
        case_table = soup.find("table", class_="searchResults")
        if not case_table:
            return []
        case_rows = case_table.findAll("tr")
        for case_row in case_rows:
            if (
                not case_row.has_key("class")
                or case_row["class"][0] == "field_4"
            ):
                continue
            cells = case_row.findAll("td")
            dob = cells[2].text.strip()
            print(dob, input_dob)
            if dob == input_dob:
                case_number = cells[0].text.strip()
                name = cells[1].text.strip()
                role = cells[3].text.strip()
                e_pay = cells[4].text.strip()
                case_url = ""
                if cells[0].find("a"):
                    case_url = self.BASE_URL + cells[0].find("a").attrs["href"]
                cases.append(
                    {
                        "case_number": case_number,
                        "name": name,
                        "dob": dob,
                        "role": role,
                        "e_pay": e_pay,
                        "case_url": case_url,
                    }
                )
        return cases

    def convertDobToStr(self, dob):
        """Convert given dob to expected dob string
        expected dob for input is 19610123 - YYYYMMDD

        This function returns string.
        """
        dobObj = datetime.strptime(dob, "%m/%d/%Y")
        return datetime.strftime(dobObj, "%B {}, %Y").format(dobObj.day)

    def search_in_johnson_il(self, first_name, last_name, dob):
        """Scrape the web site using the given search criteria.

        This function either returns an object with
        a field called "result" which is an array of cases, or
        an object with a field called "error" with a error string
        e.g. { "result": [...] } or { "error": "..." }
        """

        first_name = NameNormalizer(first_name).normalized()
        last_name = NameNormalizer(last_name).normalized()
        if dob:
            dob = dob.strip()

        dob_string = self.convertDobToStr(dob)
        print(dob_string)

        try:
            r = self.GLOBAL_SESSION.get(
                self.SEARCH_RESULT_PAGE_URL.format(
                    self.COURT_ID, last_name + "%2C+" + first_name, 0
                )
            )
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {"error": str(e)}

        soup = BeautifulSoup(r.text, features="html.parser")
        last_page_link = soup.find("a", class_="last")

        cases = []
        if last_page_link:
            last_page = int(last_page_link.attrs["href"].split("&offset=")[1])
            print(last_page)
            for page in range(0, last_page + 1):
                try:
                    r = self.GLOBAL_SESSION.get(
                        self.SEARCH_RESULT_PAGE_URL.format(
                            self.COURT_ID,
                            last_name + "%2C+" + first_name,
                            page,
                        )
                    )
                except requests.ConnectionError as e:
                    print("Connection failure : " + str(e))
                    print("Verification with InsightFinder credentials Failed")
                    return {"error": str(e)}
                soup = BeautifulSoup(r.text, features="html.parser")
                cases = cases + self.parse_search_results(soup, dob_string)
        else:
            cases = self.parse_search_results(soup, dob_string)

        for case in cases:
            if case["case_url"] != "":
                case["case_detail"] = self.get_case_detail(case["case_url"])

        return {"result": cases}


if __name__ == "__main__":
    print(
        json.dumps(
            ScraperILJohnsonSuperior().scrape(
                search_parameters={
                    "firstName": "Richard",
                    "lastName": "Smith",
                    "dob": "12/27/1978",
                }
            )["result"],
            indent=4,
            sort_keys=True,
        )
    )
    print("Done running", __file__, ".")
