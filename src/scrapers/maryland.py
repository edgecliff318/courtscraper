""" Scraper for Maryland State Court """
import json
import os.path
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from src.scrapers.base import InitializedSession, NameNormalizer, ScraperBase

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    + "/libraries"
)

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
)


class ScraperMDCourt(ScraperBase):
    """MD Court scraper"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate",
    }
    BASE_URL = "http://casesearch.courts.state.md.us/casesearch/"
    DISCLAIMER_URL = (
        "http://casesearch.courts.state.md.us/casesearch/processDisclaimer.jis"
    )
    SEARCH_RESULT_URL = "http://casesearch.courts.state.md.us/casesearch/inquiry-results.jsp?d-16544-p={}&lastName={}&filingDate=&filingEnd=&partyType=&courtSystem=B&courttype=N&firstName={}&site=00&filingStart=&action=Search&company=N&middleName=&countyName="
    FIRST_SEARCH_URL = (
        "http://casesearch.courts.state.md.us/casesearch/inquirySearch.jis"
    )

    def scrape(self, search_parameters):
        """Entry point for lambda.

        Query should look like this:

        {
            "lastName": "Smith",
            "firstName": "Adam",
            "dob": "10/06/1969"
        }
        https://<endpoint>?queryStringParameters
        """

        last_name = search_parameters["lastName"]
        first_name = search_parameters["firstName"]
        dob = search_parameters["dob"]
        return self.search_in_md(first_name, last_name, dob)

    GLOBAL_SESSION = InitializedSession(headers=HEADERS)

    def get_case_detail(self, soup):
        """Get every information of case detail by parsing rendered HTML page

        This function returns an object.
        """
        case_detail = {}
        detail_body = soup.find("div", class_="BodyWindow")
        status = ""
        substatus = ""
        if detail_body:
            children = detail_body.findChildren()
            for child in children:
                if (
                    child.text.strip() == "Case Information"
                    or child.text.strip() == "Defendant Information"
                    or child.text.strip() == "Involved Parties Information"
                    or child.text.strip()
                    == "Charge and Disposition Information"
                    or child.text.strip() == "Bond Setting Information"
                    or child.text.strip() == "Document Information"
                    or child.text.strip() == "Other Reference Numbers"
                    or child.text.strip() == "Causes Information"
                    or child.text.strip() == "Judgment Information"
                    or child.text.strip() == "Case Judgment Comment History"
                ):
                    status = child.text.strip()

                if status == "Case Information":
                    if "Case Information" not in case_detail:
                        case_detail["Case Information"] = {}
                    if "Court System:" in child.text.strip():
                        rows = child.findAll("tr")
                        for row in rows:
                            if len(row.findAll("td")) > 1:
                                key = (
                                    row.findAll("td")[0]
                                    .text.replace(":", "")
                                    .strip()
                                )
                                value = (
                                    row.findAll("td")[1]
                                    .text.replace("\n", " ")
                                    .replace("\t", "")
                                    .strip()
                                )
                                if key != "":
                                    case_detail["Case Information"][
                                        key
                                    ] = value
                elif status == "Defendant Information":
                    if "Defendant Information" not in case_detail:
                        case_detail["Defendant Information"] = {}
                    if child.text.strip() == "Defendant":
                        substatus = child.text.strip()
                    if substatus == "Defendant":
                        if (
                            "Defendant"
                            not in case_detail["Defendant Information"]
                        ):
                            case_detail["Defendant Information"][
                                "Defendant"
                            ] = {}
                        spans = child.findAll("span")
                        if len(spans) > 0 and len(spans) % 2 == 0:
                            for i in range(0, len(spans)):
                                if i % 2 == 0:
                                    key = (
                                        spans[i].text.replace(":", "").strip()
                                    )
                                    value = spans[i + 1].text.strip()
                                    if key != "":
                                        case_detail["Defendant Information"][
                                            "Defendant"
                                        ][key] = value
                elif status == "Involved Parties Information":
                    if "Involved Parties Information" not in case_detail:
                        case_detail["Involved Parties Information"] = {}
                        substatus = ""
                    if (
                        child.text.strip() == "Attorney(s) for the Plaintiff"
                        or child.text.strip() == "Plaintiff"
                        or child.text.strip() == "Bond Remitter/Bondsman"
                        or child.text.strip()
                        == "Officer - Arresting/Complainant"
                        or child.text.strip() == "Bond Remitter/Bondsman"
                    ):
                        substatus = child.text.strip()
                        case_detail["Involved Parties Information"][
                            substatus
                        ] = {}
                    spans = child.findAll("span")
                    if (
                        len(spans) > 0
                        and len(spans) % 2 == 0
                        and substatus != ""
                    ):
                        for i in range(0, len(spans)):
                            if i % 2 == 0:
                                key = spans[i].text.replace(":", "").strip()
                                value = spans[i + 1].text.strip()
                                if key != "":
                                    case_detail[
                                        "Involved Parties Information"
                                    ][substatus][key] = value
                elif status == "Charge and Disposition Information":
                    if "Charge and Disposition Information" not in case_detail:
                        case_detail["Charge and Disposition Information"] = []
                    if (
                        child.has_key("class")
                        and child["class"][0] == "AltBodyWindow1"
                    ):
                        spans = child.findAll("span")
                        obj = {}
                        if len(spans) > 0 and len(spans) % 2 == 0:
                            for i in range(0, len(spans)):
                                if i % 2 == 0:
                                    key = (
                                        spans[i].text.replace(":", "").strip()
                                    )
                                    value = spans[i + 1].text.strip()
                                    if key != "":
                                        obj[key] = value
                        case_detail[
                            "Charge and Disposition Information"
                        ].append(obj)
                elif status == "Bond Setting Information":
                    if "Bond Setting Information" not in case_detail:
                        case_detail["Bond Setting Information"] = []
                    spans = child.findAll("span")
                    if child.name == "table" and len(spans) > 0:
                        obj = {}
                        for i in range(0, len(spans)):
                            if i % 2 == 0:
                                key = spans[i].text.replace(":", "").strip()
                                value = spans[i + 1].text.strip()
                                if key != "":
                                    obj[key] = value
                        case_detail["Bond Setting Information"].append(obj)
                elif status == "Document Information":
                    if "Document Information" not in case_detail:
                        case_detail["Document Information"] = []
                    spans = child.findAll("span")
                    if child.name == "table" and len(spans) > 0:
                        obj = {}
                        for i in range(0, len(spans)):
                            if i % 2 == 0:
                                if i + 1 < len(spans):
                                    key = (
                                        spans[i].text.replace(":", "").strip()
                                    )
                                    value = spans[i + 1].text.strip()
                                    if key != "":
                                        obj[key] = value
                        case_detail["Document Information"].append(obj)
                elif status == "Other Reference Numbers":
                    if "Other Reference Numbers" not in case_detail:
                        case_detail["Other Reference Numbers"] = {}
                    spans = child.findAll("span")
                    if child.name == "table" and len(spans) > 0:
                        for i in range(0, len(spans)):
                            if i % 2 == 0:
                                key = spans[i].text.replace(":", "").strip()
                                value = spans[i + 1].text.strip()
                                if (
                                    key == "Same Incident"
                                    and key
                                    not in case_detail[
                                        "Other Reference Numbers"
                                    ]
                                ):
                                    case_detail["Other Reference Numbers"][
                                        key
                                    ] = []
                                if key != "":
                                    if key == "Same Incident":
                                        case_detail["Other Reference Numbers"][
                                            key
                                        ].append(value)
                                    else:
                                        case_detail["Other Reference Numbers"][
                                            key
                                        ] = value
                elif status == "Causes Information":
                    if "Causes Information" not in case_detail:
                        case_detail["Causes Information"] = {}
                    if child.name == "table":
                        if child.find("tr", class_="RowColorOne"):
                            rows = child.findAll("tr")
                            count = 0
                            case_detail["Causes Information"]["Remedy"] = []
                            for row in rows:
                                if count > 0:
                                    case_detail["Causes Information"][
                                        "Remedy"
                                    ].append(
                                        {
                                            "Remedy Type": row.findAll("td")[
                                                0
                                            ].text.strip(),
                                            "Amount": row.findAll("td")[
                                                1
                                            ].text.strip(),
                                            "Comment": row.findAll("td")[
                                                2
                                            ].text.strip(),
                                        }
                                    )
                                count = count + 1
                        else:
                            spans = child.findAll("span")
                            for i in range(0, len(spans)):
                                if i % 2 == 0:
                                    key = (
                                        spans[i].text.replace(":", "").strip()
                                    )
                                    value = spans[i + 1].text.strip()
                                    if key != "":
                                        case_detail["Causes Information"][
                                            key
                                        ] = value
                elif status == "Judge Information":
                    if "Judge Information" not in case_detail:
                        case_detail["Judge Information"] = {}
                    if child.name == "table":
                        if child.find("tr", class_="RowColorOne"):
                            rows = child.findAll("tr")
                            count = 0
                            case_detail["Judge Information"]["Judgement"] = []
                            for row in rows:
                                if count > 0:
                                    case_detail["Judge Information"][
                                        "Judgement"
                                    ].append(
                                        {
                                            "Judgement Status": row.findAll(
                                                "td"
                                            )[0].text.strip(),
                                            "Status Date": row.findAll("td")[
                                                1
                                            ].text.strip(),
                                        }
                                    )
                                count = count + 1
                        else:
                            spans = child.findAll("span")
                            for i in range(0, len(spans)):
                                if i % 2 == 0:
                                    key = (
                                        spans[i].text.replace(":", "").strip()
                                    )
                                    value = spans[i + 1].text.strip()
                                    if key != "":
                                        case_detail["Judge Information"][
                                            key
                                        ] = value
                elif status == "Case Judgment Comment History":
                    if child.name == "table":
                        case_detail[
                            "Case Judgment Comment History"
                        ] = child.text.strip()
        # print(json.dumps(case_detail, indent=4, sort_keys=True))
        return case_detail

    def parse_search_results_by_page(self, soup):
        """Parse Search Result Page(only one page) and get cases

        This function returns an array.
        """
        cases = []
        case_table = soup.find("table", class_="results")
        if not case_table:
            return []
        case_rows = case_table.findAll(
            "tr", class_="odd"
        ) + case_table.findAll("tr", class_="even")
        for case_row in case_rows:
            cells = case_row.findAll("td")
            if len(cells) > 8:
                case_number = cells[0].text.strip()
                name = cells[1].text.strip()
                date_of_birth = cells[2].text.strip()
                party_type = cells[3].text.strip()
                court = cells[4].text.strip()
                case_type = cells[5].text.strip()
                case_status = cells[6].text.strip()
                filing_date = cells[7].text.strip()
                case_caption = cells[8].text.strip()

                case_url = ""
                if cells[0].find("a"):
                    case_url = cells[0].find("a").attrs["href"]

                cases.append(
                    {
                        "case_number": case_number,
                        "name": name,
                        "date_of_birth": date_of_birth,
                        "party_type": party_type,
                        "court": court,
                        "case_type": case_type,
                        "case_status": case_status,
                        "filing_date": filing_date,
                        "case_caption": case_caption,
                        "case_url": case_url,
                    }
                )
        return cases

    def search_in_md(self, first_name, last_name, dob):
        """Scrape the web site using the given search criteria.

        This function either returns an object with
        a field called "result" which is an array of cases, or
        an object with a field called "error" with a error string
        e.g. { "result": [...] } or { "error": "..." }
        """

        first_name = NameNormalizer(first_name).normalized()
        last_name = NameNormalizer(last_name).normalized()
        year = ""
        month = ""
        if dob:
            dob = dob.strip()
            objDob = datetime.strptime(dob, "%m/%d/%Y")
            year = str(objDob.year)
            month = str(objDob.month)

        print(year, month)
        try:
            r = self.GLOBAL_SESSION.get(self.BASE_URL)
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {"error": str(e)}

        try:
            r = self.GLOBAL_SESSION.post(
                self.DISCLAIMER_URL, {"disclaimer": "Y", "action": "Continue"}
            )
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {"error": str(e)}

        try:
            r = self.GLOBAL_SESSION.post(
                self.FIRST_SEARCH_URL,
                {
                    "lastName": last_name,
                    "firstName": first_name,
                    "middleName": "",
                    "exactMatchLn": "Y",
                    "partyType": "",
                    "site": "00",
                    "courtSystem": "B",
                    "countyName": "",
                    "filingStart": "",
                    "filingEnd": "",
                    "filingDate": "",
                    "company": "N",
                    "courttype": "N",
                    "action": "Search",
                },
            )
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {"error": str(e)}

        soup = BeautifulSoup(r.text, features="html.parser")

        if soup.find("span", class_="pagebanner"):
            # get total count of search results
            total_count = int(
                soup.find("span", class_="pagebanner")
                .text.split("item")[0]
                .strip()
            )
            page_count = 1

            # calculate the page count(25 cases per page)
            if total_count - int(total_count / 25) * 25 > 0:
                page_count = int(total_count / 25) + 1
            else:
                page_count = int(total_count / 25)
            print(page_count)
            result = []

            # get cases page by page
            for page in range(1, page_count + 1):
                print("=================={}===================".format(page))
                try:
                    r = self.GLOBAL_SESSION.get(
                        self.SEARCH_RESULT_URL.format(
                            page, first_name, last_name
                        )
                    )
                except requests.ConnectionError as e:
                    print("Connection failure : " + str(e))
                    print("Verification with InsightFinder credentials Failed")
                    return {"error": str(e)}
                soup = BeautifulSoup(r.text, features="html.parser")
                page_result = self.parse_search_results_by_page(soup)
                for case in page_result:
                    print(case["case_number"])
                    if (
                        year == "" and month == ""
                    ):  # there is on dob in params get all cases
                        result.append(case)
                    else:
                        # filter case with given dob year and month
                        if self.dob_matches(
                            case["date_of_birth"], year, month
                        ):
                            print(case)
                            try:
                                r = self.GLOBAL_SESSION.get(
                                    self.BASE_URL + case["case_url"]
                                )
                            except requests.ConnectionError as e:
                                print("Connection failure : " + str(e))
                                print(
                                    "Verification with InsightFinder credentials Failed"
                                )
                                return {"error": str(e)}

                            soup = BeautifulSoup(
                                r.text, features="html.parser"
                            )
                            case["case_detail"] = self.get_case_detail(soup)
                            result.append(case)
            return {"result": result}
        else:
            return {"error": "No Result"}

    def dob_matches(self, dob, year, month):
        """Returns true if the given dob year and month match the given dob."""
        if dob != "":
            print(
                dob.split("/")[0].strip(),
                dob.split("/")[1].strip(),
                month,
                year,
            )
        return (
            dob != ""
            and dob.split("/")[0].strip() == month
            and dob.split("/")[1].strip() == year
        )


if __name__ == "__main__":
    print(
        json.dumps(
            ScraperMDCourt().scrape(
                search_parameters={
                    "firstName": "Adam",
                    "lastName": "Smith",
                    "dob": "10/06/1969",
                }
            )["result"],
            indent=4,
            sort_keys=True,
        )
    )
    print("Done running", __file__, ".")
