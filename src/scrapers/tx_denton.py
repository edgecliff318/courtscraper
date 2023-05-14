""" Scraper for Denton Justice Court """
import json
import os.path
import sys

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


class ScraperTXDentonJustice(ScraperBase):
    """TX Denton Justice Court scraper"""

    HEADERS = {
        "Content-Type": "application/x-www-form-urlencoded",
        # 'Cookie': 'ASP.NET_SessionId=hd10mr45gd05og452wswf321; .ASPXFORMSPUBLICACCESS=A2E297C1CA473DC8728BB54CC4B99D141491D13CF64A38BBF834A23F0B82834650DE9FF9258C2F30CA3F43F64F131C77762CE4470B04AD11826F2AF471D7FD9CAEBD8FABF447D570CEB1471D03FCA0E29712EE2ADE0F0190F629BD7746082D909C4DB7F34CE5F5DCF6D000535CD1044F4B8B5F98DC815677AFCFCAD6B5CB9AB3D52391214F5D18F6B73E2650FE52DCB4A2FF3116'
    }
    LOGIN_URL = "https://justice1.dentoncounty.gov/PublicAccess/login.aspx"
    BASE_URL = "https://justice1.dentoncounty.gov/PublicAccess/"
    HOME_URL = "https://justice1.dentoncounty.gov/PublicAccess/default.aspx"
    SEARCH_RESULT_URL = (
        "https://justice1.dentoncounty.gov/PublicAccess/Search.aspx?ID=100"
    )

    def scrape(self, search_parameters):
        """Entry point for lambda.

        Query should look like this:

        {
            "lastName": "John",
            "firstName": "Washington",
            "dob": ""
        }
        https://<endpoint>?queryStringParameters
        """
        last_name = search_parameters["lastName"]
        first_name = search_parameters["firstName"]
        dob = search_parameters["dob"]
        return self.search_in_denton_tx(first_name, last_name, dob)

    GLOBAL_SESSION = InitializedSession(headers=HEADERS)

    def get_case_detail(self, soup):
        """Get every information of case detail by parsing rendered HTML page

        This function returns an object.
        """
        case_detail = {}
        status = ""
        for row in soup.findAll("tr"):
            data_cells = row.findAll("td")
            if (
                row.find("th", class_="ssTableHeaderLabel")
                and len(data_cells) == 1
            ):
                case_detail[
                    row.find("th", class_="ssTableHeaderLabel")
                    .text.replace(":", "")
                    .strip()
                ] = data_cells[0].text.strip()
                continue

            if (
                len(row.findAll("th", class_="ssTableHeader")) == 2
                and "Defendant"
                in row.findAll("th", class_="ssTableHeader")[0].text
            ):
                status = "Defendant"
                case_detail["Defendant"] = row.findAll(
                    "th", class_="ssTableHeader"
                )[1].text.strip()
                if len(data_cells) > 1:
                    case_detail["Dob"] = data_cells[1].text.strip()
                continue
            if status == "Defendant":
                # print(row)
                case_detail["Defendant Address"] = row.text.replace(
                    "\xa0", ""
                ).strip()
                status = ""
                continue

            if (
                len(row.findAll("th", class_="ssTableHeader")) == 2
                and "Plaintiff"
                in row.findAll("th", class_="ssTableHeader")[0].text
            ):
                case_detail["Plaintiff"] = row.findAll(
                    "th", class_="ssTableHeader"
                )[1].text.strip()
                continue

            if (
                len(row.findAll("th", class_="ssTableHeader")) > 2
                and "Statute"
                in row.findAll("th", class_="ssTableHeader")[2].text
            ):
                case_detail["Charges"] = []
                status = "Charges"
                continue

            if (
                status == "Charges"
                and len(data_cells) >= 6
                and data_cells[0].text.strip() != ""
            ):
                case_detail["Charges"].append(
                    {
                        "Charge": data_cells[1].text.strip(),
                        "Statute": data_cells[3].text.strip(),
                        "Level": data_cells[4].text.strip(),
                        "Date": data_cells[5].text.strip(),
                    }
                )
                continue

            if (
                row.find("th", class_="ssEventsAndOrdersSubTitle")
                and "DISPOSITIONS"
                in row.find("th", class_="ssEventsAndOrdersSubTitle").text
            ):
                case_detail["DISPOSITIONS"] = []
                status = "Dispositions"
                continue
            if status == "Dispositions" and row.find(
                "th", class_="ssTableHeaderLabel"
            ):
                # print(row)
                if (
                    data_cells[2].find("div")
                    and data_cells[2].find("div").find("div")
                    and data_cells[2].find("div").find("br")
                    and data_cells[2].find("div").find("div").find("div")
                    and data_cells[2].find("div").find("div").find("div")
                ):
                    key = data_cells[2].find("div").find("b").text
                    value = (
                        data_cells[2]
                        .find("div")
                        .text.replace(
                            data_cells[2].find("div").find("div").text, ""
                        )
                        .replace(data_cells[2].find("div").find("b").text, "")
                    )
                    print(data_cells[2].find("div").find("b").text, key)
                    print()
                if key and value:
                    case_detail["DISPOSITIONS"].append(
                        {
                            "Date": row.find(
                                "th", class_="ssTableHeaderLabel"
                            ).text.strip(),
                            key: value,
                            "Disposition": data_cells[2]
                            .find("div")
                            .find("div")
                            .find("div")
                            .text.replace(
                                data_cells[2]
                                .find("div")
                                .find("div")
                                .find("div")
                                .find("div")
                                .text,
                                " "
                                + data_cells[2]
                                .find("div")
                                .find("div")
                                .find("div")
                                .find("div")
                                .text,
                            ),
                        }
                    )
            if (
                row.find("th", class_="ssEventsAndOrdersSubTitle")
                and "OTHER EVENTS AND HEARINGS"
                in row.find("th", class_="ssEventsAndOrdersSubTitle").text
            ):
                case_detail["OTHER EVENTS AND HEARINGS"] = []
                status = "OTHER EVENTS AND HEARINGS"
                continue
            if status == "OTHER EVENTS AND HEARINGS" and row.find(
                "th", class_="ssTableHeaderLabel"
            ):
                case_detail["OTHER EVENTS AND HEARINGS"].append(
                    {
                        "Date": row.find(
                            "th", class_="ssTableHeaderLabel"
                        ).text.strip(),
                        "Event": data_cells[2].find("b").text.strip(),
                        "Content": data_cells[2].find("div").text.strip()
                        if data_cells[2].find("div")
                        else "",
                    }
                )
                continue
            if (
                row.find("th", class_="ssTableHeaderLabelLeft")
                and row.find("th", class_="ssTableHeaderLabelLeft").find(
                    "span"
                )
                and "Defendant"
                in row.find("th", class_="ssTableHeaderLabelLeft")
                .find("span")
                .text
            ):
                status = "Financial"
                case_detail["Financial"] = []
                continue
            if status == "Financial" and row.find(
                "th", class_="ssTableHeaderLabel"
            ):
                case_detail["Financial"].append(
                    {
                        "Date": row.find(
                            "th", class_="ssTableHeaderLabel"
                        ).text.strip(),
                        "Type": row.find(
                            "th", class_="ssTableHeaderLabelLeft"
                        ).text.strip(),
                        "Receipt": data_cells[2].text.strip(),
                        "Name": data_cells[3].text.strip(),
                        "Amount": data_cells[4].text.strip(),
                    }
                )
        return case_detail

    def parse_search_results(self, soup):
        """Parse rendered HTML page for search result and get matched cases

        This function returns an array.
        """
        cases = []
        for table in soup.findAll("table"):
            if (
                "cellpadding" in table.attrs
                and table.attrs["cellpadding"] == "2"
            ):
                rows = table.findAll("tr")
                count = 0
                for row in rows:
                    case = row.findAll("td")
                    if count > 1 and len(case) > 1:
                        if len(case[2].findAll("div")) == 2:
                            defendant_name = (
                                case[2].findAll("div")[0].text.strip()
                            )
                            defendant_dob = (
                                case[2].findAll("div")[1].text.strip()
                            )
                        else:
                            defendant_name = ""
                            defendant_dob = ""
                        if len(case[3].findAll("div")) == 3:
                            filed_date = case[3].findAll("div")[0].text.strip()
                            location = case[3].findAll("div")[1].text.strip()
                            judicial_officer = (
                                case[3].findAll("div")[2].text.strip()
                            )
                        else:
                            filed_date = ""
                            location = ""
                            judicial_officer = ""

                        if len(case[4].findAll("div")) == 2:
                            case_type = case[4].findAll("div")[0].text.strip()
                            status = case[4].findAll("div")[1].text.strip()
                        else:
                            case_type = ""
                            status = ""

                        cases.append(
                            {
                                "detail_url": self.BASE_URL
                                + case[0].find("a").attrs["href"],
                                "case_number": case[0].text.strip(),
                                "citation_number": case[1].text.strip(),
                                "defendant_name": defendant_name,
                                "defendant_dob": defendant_dob,
                                "filed_date": filed_date,
                                "location": location,
                                "judicial_officer": judicial_officer,
                                "case_type": case_type,
                                "status": status,
                                "charges": case[5].text.strip(),
                            }
                        )
                    count = count + 1
        print(cases)
        return cases

    def search_in_denton_tx(self, first_name, last_name, dob):
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

        try:
            self.GLOBAL_SESSION.get(self.HOME_URL)

            r = self.GLOBAL_SESSION.post(
                self.SEARCH_RESULT_URL,
                {
                    "__EVENTTARGET": "",
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": "/wEPDwULLTEwOTk1NTcyNzAPZBYCZg9kFgICAQ8WAh4HVmlzaWJsZWgWAgIDDw9kFgIeB29ua2V5dXAFJnRoaXMudmFsdWUgPSB0aGlzLnZhbHVlLnRvTG93ZXJDYXNlKCk7ZGQqvTJuqQJ178T+ZAZMLA3f3Jn9CQ==",
                    "__VIEWSTATEGENERATOR": "B9B0191F",
                    "__EVENTVALIDATION": "/wEWAgKvqsb/CQKYxoa5CEXDEBK48RxiGuoq7iRSiHbE5g5L",
                    "NodeID": "1,1101,1110,1102,1003,1104,1105,1106,1107,1270,1280,1310,1320,1330,1340,1350,1360",
                    "NodeDesc": "All JP & County Courts",
                    "SearchBy": "1",
                    "ExactName": "on",
                    "CaseSearchMode": "CaseNumber",
                    "CaseSearchValue": "",
                    "CitationSearchValue": "",
                    "CourtCaseSearchValue": "",
                    "PartySearchMode": "Name",
                    "AttorneySearchMode": "Name",
                    "LastName": last_name,
                    "FirstName": first_name,
                    "cboState": "AA",
                    "MiddleName": "",
                    "DateOfBirth": dob,
                    "DriverLicNum": "",
                    "CaseStatusType": "0",
                    "DateFiledOnAfter": "",
                    "DateFiledOnBefore": "",
                    "chkCriminal": "on",
                    "chkFamily": "on",
                    "chkCivil": "on",
                    "chkProbate": "on",
                    "chkDtRangeCriminal": "on",
                    "chkDtRangeFamily": "on",
                    "chkDtRangeCivil": "on",
                    "chkDtRangeProbate": "on",
                    "chkCriminalMagist": "on",
                    "chkFamilyMagist": "on",
                    "chkCivilMagist": "on",
                    "chkProbateMagist": "on",
                    "DateSettingOnAfter": "",
                    "DateSettingOnBefore": "",
                    "SortBy": "fileddate",
                    "SearchSubmit": "Search",
                    "SearchType": "PARTY",
                    "SearchMode": "NAME",
                    "NameTypeKy": "ALIAS",
                    "BaseConnKy": "DF",
                    "StatusType": "true",
                    "ShowInactive": "",
                    "AllStatusTypes": "true",
                    "CaseCategories": "",
                    "RequireFirstName": "False",
                    "CaseTypeIDs": "",
                    "HearingTypeIDs": "",
                    "SearchParams": 'Party~~Search By": "~~1~~Defendant||chkExactName~~Exact Name": "~~on~~on||PartyNameOption~~Party Search Mode": "~~Name~~Name||LastName~~Last Name": "~~{}~~{}||FirstName~~First Name": "~~{}~~{}||DateOfBirth~~Date of Birth": "~~{}~~{}||AllOption~~All~~0~~All||selectSortBy~~Sort By": "~~Filed Date~~Filed Date'.format(
                        last_name, last_name, first_name, first_name, dob, dob
                    ),
                },
            )

            soup = BeautifulSoup(r.text, features="html.parser")

            # parse html response and get the matched cases
            cases = self.parse_search_results(soup)
            for case in cases:
                r = self.GLOBAL_SESSION.get(case["detail_url"])
                soup = BeautifulSoup(r.text, features="html.parser")
                case["case_detail"] = self.get_case_detail(soup)

        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
            return {"error": str(e)}

        return {"result": cases}
        # # print(json.dumps(result, indent=4, sort_keys=True))
        # if 'error' in result:
        #     return {'error': result['error']}
        # else:
        #     return {'result': result['cases']}


if __name__ == "__main__":
    print(
        json.dumps(
            ScraperTXDentonJustice().scrape(
                search_parameters={
                    "firstName": "Adam",
                    "lastName": "Smith",
                    "dob": "03/28/1978",
                }
            )["result"],
            indent=4,
            sort_keys=True,
        )
    )
    print("Done running", __file__, ".")
