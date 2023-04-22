import datetime
import json
import logging
import time
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from pdf2image.pdf2image import convert_from_path
from requests.adapters import HTTPAdapter, Retry
from rich.progress import track

from src.core.config import get_settings
from src.loader.tickets import TicketParser
from src.models.courts import Court
from src.scrapers.base import InitializedSession, NameNormalizer, ScraperBase

settings = get_settings()

logger = logging.Logger(__name__)


class ScraperMOCourt(ScraperBase):
    """MO Court scraper"""

    HEADERS = {
        "Cookie": "JSESSIONID=0002pphbtlp7uRm6dW_INFcHuXg:-750NJ; UJID=09f039e6-57e8-40ef-80e7-a6c50fad2b77; UJIA=-1807178247; _ga=GA1.2.1302091217.1672778481; _gid=GA1.2.2076773627.1672778481; visitorid=20230103144121770562; JSESSIONID=000239F0YlUH4oSeKr1nCvAdhRg:-RG2DR; crowd.token_key=SZeXgH84SekMvZQXzCDaIg00",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    BASE_URL = "https://www.courts.mo.gov"
    CASE_NO_SEARCH_URL = "https://www.courts.mo.gov/cnet/caseNoSearch.do"
    SEARCH_RESULT_URL = "https://www.courts.mo.gov/casenet/cases/nameSearch.do"
    CASE_HEADER_URL = "https://www.courts.mo.gov/casenet/cases/header.do"
    PARTIES_URL = "https://www.courts.mo.gov/casenet/cases/parties.do"
    DOCKETS_URL = "https://www.courts.mo.gov/casenet/cases/searchDockets.do"
    SERVICE_URL = "https://www.courts.mo.gov/casenet/cases/service.do"
    CHARGES_URL = "https://www.courts.mo.gov/casenet/cases/charges.do"

    @property
    def GLOBAL_SESSION(self):
        if self._GLOBAL_SESSION is None:
            payload = (
                f"username={self.username}"
                f"&password={self.password}&logon=logon"
            )
            self._GLOBAL_SESSION = InitializedSession(
                headers=self.HEADERS,
                initial_url="https://www.courts.mo.gov/cnet/logon.do",
                payload=payload,
            )
            retries = Retry(total=5, backoff_factor=1)

            self._GLOBAL_SESSION.mount(
                "http://", HTTPAdapter(max_retries=retries)
            )
            self._GLOBAL_SESSION.mount(
                "https://www.courts.mo.gov",
                HTTPAdapter(max_retries=3),
            )
        return self._GLOBAL_SESSION

    def scrape(self, search_parameters):
        """Entry point for lambda.

        Query should look like this:

        {
            "lastName": "Montana",
            "firstName": "Tony",
            "dob": "10/06/1969"
        }
        https://<endpoint>?queryStringParameters
        """
        last_name = search_parameters["lastName"]
        first_name = search_parameters["firstName"]
        dob = search_parameters["dob"]
        return self.search_in_mo(first_name, last_name, dob)

    def get_case_header(self, soup):
        """Get case header of case detail by parsing rendered HTML page

        This function returns an object.
        """
        case_header = {}
        detail_table = soup.find("table", class_="detailRecordTable")
        if detail_table:
            key = ""
            value = ""
            for cell in detail_table.findAll("td"):
                if cell.has_attr("class"):
                    if cell["class"][0] == "detailLabels":
                        key = cell.text.strip()
                    elif cell["class"][0] == "detailData":
                        value = cell.text.strip()
                        if key != "":
                            case_header[key.replace(":", "")] = value
                        key = ""
        return case_header

    def get_case_details(self, case_number):
        data = f"courtType=&countyCode=&cortCode=SW&caseNumber={case_number}"
        response = self.GLOBAL_SESSION.post(
            self.CASE_NO_SEARCH_URL, headers=self.HEADERS, data=data
        )
        url_pars = parse_qs(urlparse(response.url).query)
        return {
            "case_number": case_number,
            "court_id": url_pars["inputVO.courtId"][0],
        }

    def get_docket_entries(self, soup):
        """Get docket entries of case detail by parsing rendered HTML page

        This function returns an array.
        """
        docket_entries = []
        detail_table = soup.find("table", class_="detailRecordTable")
        if detail_table:
            for row in detail_table.findAll("tr"):
                if row.text.replace("\n", "").replace("\t", "").strip() != "":
                    docket_entries.append(
                        row.text.replace("\n", "").replace("\t", "").strip()
                    )

        dockets = []
        for a in detail_table.find_all("a", href=True):
            try:
                content = a.find_all("b").pop().contents
            except:
                content = a.contens
            docket_url_pars = parse_qs(urlparse(a.attrs["href"]).query)
            docket_di = docket_url_pars.get("di").pop()
            docket_court_code = docket_url_pars.get("courtCode").pop()
            docket_file_url = self.BASE_URL + (
                f"/fv/c/?courtCode="
                f"{docket_court_code}"
                f"&di="
                f"{docket_di}"
            )
            try:
                docket_filepath = self.download(docket_file_url)

            except Exception as e:
                logger.error(
                    f"Failed to download and save file"
                    f" {docket_file_url} with error {e}"
                )
                docket_filepath = None
            # TODO: #2 Need a better management of docket files
            dockets.append(
                {
                    "docket_content": content,
                    "docket_number": docket_di,
                    "docket_url": self.BASE_URL + a.attrs["href"],
                    "docket_file_url": docket_file_url,
                    "docket_filepath": docket_filepath,
                }
            )
        return docket_entries, dockets

    def get_case_charges(self, soup):
        """Get charges of case detail by parsing rendered HTML page

        This function returns an array.
        """
        case_charges = {}
        detail_table = soup.find("table", class_="detailRecordTable")
        category = ""
        if detail_table:
            for row in detail_table.findAll("tr"):
                if row.find("td", class_="detailSeperator"):
                    category = row.find(
                        "td", class_="detailSeperator"
                    ).text.strip()
                    case_charges[category] = {}
                else:
                    for cell in row.findAll("td"):
                        if cell.has_attr("class"):
                            if cell["class"][0] == "detailLabels":
                                key = cell.text.strip()
                            elif cell["class"][0] == "detailData":
                                value = (
                                    cell.text.replace("\n", "")
                                    .replace("\t", "")
                                    .strip()
                                )
                                if key != "":
                                    case_charges[category][
                                        key.replace(":", "")
                                    ] = value
                                key = ""
        return case_charges

    def parse_case_service_table(self, service_tables):
        """Get one page of case services by parsing rendered HTML page

        This function returns an array.
        """
        case_services = []
        for service_table in service_tables:
            case_service = {}
            if len(service_table.findAll("table")) == 2:
                case_service["Issuance"] = {}
                case_service["Return"] = {}
                for table in service_table.findAll("table"):
                    separator = table.find(
                        "td", class_="detailSeperator"
                    ).text.strip()
                    for cell in table.findAll("td"):
                        if cell.has_attr("class"):
                            if cell["class"][0] == "detailLabels":
                                key = cell.text.strip()
                            elif cell["class"][0] == "detailData":
                                value = (
                                    cell.text.replace("\n", "")
                                    .replace("\t", "")
                                    .strip()
                                )
                                if key != "":
                                    case_service[separator][
                                        key.replace(":", "")
                                    ] = value
                                key = ""
                    case_services.append(case_service)
        return case_services

    def get_case_service(self, soup, case):
        """Get all case services of case detail by parsing rendered HTML page

        This function returns an array.
        """
        case_services = []
        result_description = soup.find("td", class_="resultDescription")
        if result_description:
            total_count = int(
                result_description.text.strip()
                .split("of")[1]
                .split("service ")[0]
                .strip()
            )
        else:
            return case_services
        if total_count > 2:
            startingRecord = 1
            while startingRecord <= total_count:
                try:
                    r = self.GLOBAL_SESSION.post(
                        self.SERVICE_URL,
                        {
                            "inputVO.caseNumber": case["case_number"],
                            "inputVO.courtId": case["court_id"],
                            "inputVO.totalRecords": total_count,
                            "inputVO.startingRecord": startingRecord,
                        },
                    )
                except requests.ConnectionError as e:
                    logger.error("Connection failure : " + str(e))
                    logger.error(
                        "Verification with InsightFinder credentials Failed"
                    )

                if r:
                    soup = BeautifulSoup(r.text, features="html.parser")
                    service_tables = soup.findAll(
                        "table", class_="detailRecordTable"
                    )
                    case_services = (
                        case_services
                        + self.parse_case_service_table(service_tables)
                    )
                startingRecord = startingRecord + 2
        else:
            service_tables = soup.findAll("table", class_="detailRecordTable")
            case_services = self.parse_case_service_table(service_tables)

        return case_services

    def get_case_info(self, case):
        """Get every information of case detail by parsing rendered HTML page

        This function returns an object.
        """
        case_detail = {}
        try:
            case_detail["details"] = self.get_case_details(case["case_number"])
        except requests.ConnectionError as e:
            logger.error(f"Connection failure : {str(e)}")
            raise ValueError(f"Case not found : {case['case_number']}")
        case["court_id"] = case_detail["details"]["court_id"]
        try:
            r = self.GLOBAL_SESSION.post(
                self.CASE_HEADER_URL,
                {
                    "inputVO.caseNumber": case["case_number"],
                    "inputVO.courtId": case["court_id"],
                },
            )
        except requests.ConnectionError as e:
            logger.error("Connection failure : " + str(e))
            logger.error("Verification with InsightFinder credentials Failed")
            case_detail["case_header"] = {}

        if r:
            soup = BeautifulSoup(r.text, features="html.parser")
            case_detail["case_header"] = self.get_case_header(soup)
            r = None

        try:
            r = self.GLOBAL_SESSION.post(
                self.PARTIES_URL,
                {
                    "inputVO.caseNumber": case["case_number"],
                    "inputVO.courtId": case["court_id"],
                },
            )
        except requests.ConnectionError as e:
            logger.error("Connection failure : " + str(e))
            logger.error("Verification with InsightFinder credentials Failed")
            case_detail["parties"] = ""

        if r:
            case_detail["parties"] = ""
            soup = BeautifulSoup(r.text, features="html.parser")
            if soup.find("table", class_="detailRecordTable"):
                case_detail["parties"] = (
                    soup.find("table", class_="detailRecordTable")
                    .text.replace("\r\n", "")
                    .replace("\t", "")
                    .strip()
                )

        try:
            r = self.GLOBAL_SESSION.post(
                self.DOCKETS_URL,
                {
                    "inputVO.caseNumber": case["case_number"],
                    "inputVO.courtId": case["court_id"],
                },
            )
        except requests.ConnectionError as e:
            logger.error("Connection failure : " + str(e))
            logger.error("Verification with InsightFinder credentials Failed")
            case_detail["dockets"] = {}

        if r:
            soup = BeautifulSoup(r.text, features="html.parser")
            (
                case_detail["dockets_links"],
                case_detail["dockets"],
            ) = self.get_docket_entries(soup)
            case_detail["ticket"] = self.parse_ticket(
                case_detail["dockets"], case["case_number"]
            )
            r = None

        try:
            r = self.GLOBAL_SESSION.post(
                self.SERVICE_URL,
                {
                    "inputVO.caseNumber": case["case_number"],
                    "inputVO.courtId": case["court_id"],
                },
            )
        except requests.ConnectionError as e:
            logger.error("Connection failure : " + str(e))
            logger.error("Verification with InsightFinder credentials Failed")
            case_detail["services"] = {}

        if r:
            soup = BeautifulSoup(r.text, features="html.parser")
            case_detail["services"] = self.get_case_service(soup, case)
            r = None

        try:
            r = self.GLOBAL_SESSION.post(
                self.CHARGES_URL,
                {
                    "inputVO.caseNumber": case["case_number"],
                    "inputVO.courtId": case["court_id"],
                },
            )
        except requests.ConnectionError as e:
            logger.error("Connection failure : " + str(e))
            logger.error("Verification with InsightFinder credentials Failed")
            case_detail["charges"] = {}

        if r:
            soup = BeautifulSoup(r.text, features="html.parser")
            case_detail["charges"] = self.get_case_charges(soup)
            r = None
        return case_detail

    def get_identity(self, name):
        first_name = None
        last_name = None
        middle_name = None
        if len(name) > 1:
            name = name[0]
            try:
                first_name = " ".join(name.split(", ")[1:])
                r = first_name.split(" ")
                if len(r) >= 2:
                    first_name = r[0]
                    middle_name = r[1]
                else:
                    middle_name = ""
                last_name = " ".join(name.split(", ")[:1])
            except Exception:
                first_name = None
                last_name = None
        return first_name, last_name, middle_name

    def parse_case(self, case, case_type, court, date):
        # Parsing the case form casenet
        case_id = case.get("caseNumber")

        # Getting the case info
        case_info = {
            "case_number": case_id,
            "case_id": case_id,
            "case_type": case_type,
            "court_code": court.code,
            "case_date": date.replace("%2F", "/"),
            "first_name": "",
            "last_name": "",
            "age": "",
            "year_of_birth": "",
            "charges": "",
            "details": "",
            "email": "",
        }
        first_name = None
        last_name = None
        year_of_birth = None

        # Getting extra case details
        case_detail = self.get_case_info(case_info)

        try:
            # Getting all the details
            case_info["charges"] = (
                case_detail.get("charges", {})
                .get("Charge/Judgment", {})
                .get("Description", " ")
            )
            # TODO: Add parsing at this stage to remove special characters

            # Parse extra details
            case_info["dockets"] = case_detail.get("dockets", {})
            case_info["services"] = case_detail.get("services", {})
            case_info["judge"] = case_detail.get("case_header", {}).get(
                "Judge/Commissioner Assigned"
            )
            case_info["ticket"] = case_detail.get("ticket", {})
            case_info["parties"] = case_detail.get("parties", "")
            case_info["headers"] = case_detail.get("case_header", {})
            case_info["state"] = "Missouri"
            case_info["disposition"] = case_detail.get("case_header", {}).get(
                "Disposition"
            )
            case_info["date_filed"] = case_detail.get("case_header", {}).get(
                "Date Filed"
            )
            case_info["location"] = case_detail.get("case_header", {}).get(
                "Location"
            )
            case_info.update(case_detail.get("case_ticket", {}))

        except Exception as e:
            logger.error(
                f"Failed to retrieve information for case"
                f" from CaseNet "
                f"{case_id} - error {e}"
            )
            raise e
        logger.info(f"Succeeded to get details for case " f"{case_id}")

        try:
            first_name, last_name, middle_name = self.get_identity(
                case_detail["parties"].split(", Defendant")
            )
            year_of_birth, age = self.get_birthdate(case_detail, case_id)
            case_info["first_name"] = first_name
            case_info["last_name"] = last_name
            case_info["middle_name"] = middle_name
            case_info["age"] = age
            case_info["year_of_birth"] = year_of_birth
            case_info["lead_details"] = False

        except Exception as e:
            logger.debug(
                f"Failed to retrieve information "
                f"for case from BeenVerified "
                f"{case_id} - error {e}"
            )
        # Sleep for 2 seconds to avoid being blocked by the website
        time.sleep(5)
        return case_info

    def get_cases(
        self, court: Court, date, case_type="Infraction", cases_ignore=None
    ):
        date = (
            datetime.datetime.fromisoformat(date)
            .strftime("%m %d %Y")
            .replace(" ", "%2F")
        )

        session = requests.Session()
        payload = (
            '{"draw":1,"columns":[{"data":0,"name":"",'
            '"searchable":true,"orderable":true,"search":{'
            '"value":"","regex":false}},'
            '{"data":"initFiling","name":"",'
            '"searchable":true,"orderable":true,"search":{'
            '"value":"","regex":false}},'
            '{"data":"caseNumber","name":"",'
            '"searchable":true,"orderable":true,"search":{'
            '"value":"","regex":false}},{"data":"caseStyle",'
            '"name":"","searchable":true,"orderable":true,'
            '"search":{"value":"","regex":false}},'
            '{"data":"caseType","name":"","searchable":true,'
            '"orderable":true,"search":{"value":"",'
            '"regex":false}},{"data":"countyDesc","name":"",'
            '"searchable":true,"orderable":true,"search":{'
            '"value":"","regex":false}}],"order":[{'
            '"column":0,"dir":"asc"}],"start":10,'
            '"length":10,"search":{"value":"",'
            '"regex":false}}'
        )

        url = (
            f"https://www.courts.mo.gov/cnet/searchResult.do?"
            f"countyCode={court.county_code}"
            f"&courtCode={court.code}"
            f"&startDate={date}"
            f"&caseStatus=P"
            f"&caseType={case_type}"
            f"&locationCode="
        )

        session.headers.update(
            {
                "Connection": "keep-alive",
                "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="96", '
                '"Google Chrome";v="96"',
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/json;charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "sec-ch-ua-mobile": "?0",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X "
                "10_15_7) AppleWebKit/537.36 (KHTML, "
                "like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                "sec-ch-ua-platform": '"macOS"',
                "Origin": "https://www.courts.mo.gov",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            }
        )
        response = session.request(
            "POST",
            url,
            data=payload,
        )

        if cases_ignore is None:
            cases_ignore = []

        try:
            response_json = response.json()
            cases_data = response_json.get("data", [])
            logger.info(
                f"Got {response_json.get('recordsTotal')} cases from CaseNet"
            )

            cases_to_scrape = [
                case
                for case in cases_data
                if case.get("caseNumber") not in cases_ignore
            ]
        except Exception as e:
            logger.error(
                f"Failed to retrieve cases from CaseNet "
                f"for {court.name} - error {e} - url {url}"
            )
            raise e

        return [
            self.parse_case(case, case_type, court, date)
            for case in track(cases_to_scrape)
        ]

    def get_birthdate(self, results, case_id):
        year_of_birth = results["parties"].split("Year of Birth: ")
        age = None
        if len(year_of_birth) > 1:
            try:
                year_of_birth = int(year_of_birth[-1].split("\n")[-1])
                age = datetime.date.today().year - year_of_birth

            except Exception as e:
                logger.error(
                    f"Failed to get age for case" f" {case_id} - error {e}"
                )
                year_of_birth = None
                age = None
        return year_of_birth, age

    def parse_search_results(self, soup):
        """Parse Search Result Page(only one page) and get cases

        This function returns an array.
        """
        cases = []
        rows = soup.findAll("tr")
        case = {}
        for row in rows:
            if (
                "align" in row.attrs
                and row.attrs["align"] == "left"
                and not row.find("td", class_="header")
            ):
                cells = row.findAll("td")
                if len(row.findAll("td")) == 7:
                    case["party_name"] = cells[1].text.strip()
                    case["case_number"] = cells[2].text.strip()
                    case["court_id"] = ""
                    logger.info(case["case_number"])
                    if len(cells[2].find("a").attrs["href"].split("',")) == 2:
                        case["court_id"] = (
                            cells[2]
                            .find("a")
                            .attrs["href"]
                            .split("',")[1]
                            .replace("');", "")
                            .replace("'", "")
                            .strip()
                        )
                    case["party_type"] = cells[3].text.strip()
                    case["style_of_case"] = cells[4].text.strip()
                    case["case_type"] = cells[5].text.strip()
                    case["filing_date"] = cells[6].text.strip()
                else:
                    case["address_on_file"] = cells[0].text.strip()
                    case["circuit"] = cells[1].text.strip()
                    case["county"] = cells[2].text.strip()
                    case["location"] = cells[3].text.strip()
                    cases.append(case)
                    case = {}
        return cases

    def search_in_mo(self, first_name, last_name, dob):
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
            r = self.GLOBAL_SESSION.post(
                self.SEARCH_RESULT_URL,
                {
                    "inputVO.lastName": last_name,
                    "inputVO.firstName": first_name,
                },
            )
        except requests.ConnectionError as e:
            logger.error("Connection failure : " + str(e))
            logger.error("Verification with InsightFinder credentials Failed")
            return {"error": str(e)}

        soup = BeautifulSoup(r.text, features="html.parser")
        result_description = soup.find("td", class_="resultDescription")

        if not result_description:
            return {"error": "No Result"}
        total_count = int(
            result_description.text.strip()
            .split("of")[1]
            .split("records ")[0]
            .strip()
        )
        if total_count <= 8:
            # parse html response and get the matched cases
            cases = self.parse_search_results(soup)
            for case in cases:
                case["case_detail"] = self.get_case_info(case)
        else:
            startingRecord = 1
            cases = []
            while startingRecord <= total_count:
                try:
                    r = self.GLOBAL_SESSION.post(
                        self.SEARCH_RESULT_URL,
                        {
                            "inputVO.subAction": "search",
                            "inputVO.type": "SW",
                            "inputVO.courtId": "SW",
                            "inputVO.totalRecord": "0",
                            "inputVO.blockNo": "0",
                            "inputVO.selectedStatus": "A",
                            "inputVO.aliasFlag": "N",
                            "inputVO.judgmentAgainstFlag": "N",
                            "inputVO.selectedIndexCourt": "0",
                            "courtId": "SW",
                            "inputVO.lastName": last_name,
                            "inputVO.firstName": first_name,
                            "inputVO.middleName": "",
                            "inputVO.caseType": "All",
                            "inputVO.yearFiled": "",
                            "inputVO.startingRecord": startingRecord,
                            "inputVO.totalRecords": total_count,
                        },
                    )
                except requests.ConnectionError as e:
                    logger.error("Connection failure : " + str(e))
                    logger.error(
                        "Verification with InsightFinder credentials Failed"
                    )
                if r:
                    soup = BeautifulSoup(r.text, features="html.parser")
                    page_cases = self.parse_search_results(soup)
                    for case in page_cases:
                        case["case_detail"] = self.get_case_info(case)
                        cases.append(case)
                startingRecord = startingRecord + 8

        return {"result": cases}
        # print(json.dumps(result, indent=4, sort_keys=True))
        # if 'error' in result:
        #     return {'error': result['error']}
        # else:
        #     return {'result': result['cases']}

    def download(self, link):
        """Download the pdf file from the given link."""
        filepath = settings.DATA_PATH.joinpath(link.split("/")[-1] + ".pdf")
        with open(filepath, "wb") as f:
            r = self.GLOBAL_SESSION.get(link, stream=True)
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()
        logger.info(f"File saved to {filepath}")

        try:
            files = {"file": open(filepath, "rb")}
            if not settings.PRODUCTION:
                data = requests.post(
                    settings.REMOTE_DATA_UPLOAD_URL, files=files
                )
        except Exception as e:
            logger.error(f"Error uploading file to remote server : {e}")
        return str(filepath)

    def parse_ticket(self, docket_links, case_number):
        for docket in docket_links:
            if (
                "citation"
                in docket.get(
                    "docket_content",
                    [
                        "",
                    ],
                )[0].lower()
            ):
                docket_filepath = docket.get("docket_filepath")
                try:
                    images = convert_from_path(docket_filepath)
                    if images:
                        image = images[0]
                        docket_image_filepath = settings.DATA_PATH.joinpath(
                            f"{case_number}.png"
                        )
                        image.save(docket_image_filepath, "PNG")
                        ticket_parser = TicketParser(
                            filename=None,
                            input_file_path=docket_image_filepath,
                            output_file_path=settings.DATA_PATH.joinpath(
                                f"{case_number}.json"
                            ),
                        )
                        try:
                            files = {"file": open(docket_image_filepath, "rb")}
                            if not settings.PRODUCTION:
                                data = requests.post(
                                    settings.REMOTE_DATA_UPLOAD_URL,
                                    files=files,
                                )
                        except Exception as e:
                            logger.error(
                                f"Error uploading file to remote server : {e}"
                            )
                        return ticket_parser.parse()
                except Exception as e:
                    logger.error(e)
                    return {"error": "Failed to parse ticket"}


if __name__ == "__main__":
    case = {"case_number": "210555271"}

    print(
        json.dumps(
            ScraperMOCourt().get_case_info(case), indent=4, sort_keys=True
        )
    )
    print("Done running", __file__, ".")

    print("Done running", __file__, ".")
