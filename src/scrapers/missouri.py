import datetime
import json
import logging
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter, Retry
from rich.console import Console

from src.core.config import get_settings
from src.models.courts import Court
from src.scrapers.base import InitializedSession, ScraperBase

settings = get_settings()

logger = logging.Logger(__name__)

console = Console()


class ScraperMOCourt(ScraperBase):
    """MO Court scraper"""

    HEADERS = {
        "Cookie": "JSESSIONID=0002pphbtlp7uRm6dW_INFcHuXg:-750NJ; UJID=09f039e6-57e8-40ef-80e7-a6c50fad2b77; UJIA=-1807178247; _ga=GA1.2.1302091217.1672778481; _gid=GA1.2.2076773627.1672778481; visitorid=20230103144121770562; JSESSIONID=000239F0YlUH4oSeKr1nCvAdhRg:-RG2DR; crowd.token_key=SZeXgH84SekMvZQXzCDaIg00",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    BASE_URL = "https://www.courts.mo.gov"
    CASE_NO_SEARCH_URL = (
        "https://www.courts.mo.gov/cnet/cases/newHeaderData.do"
    )
    PARTIES_URL = "https://www.courts.mo.gov/cnet/cases/party.do"
    CHARGES_URL = "https://www.courts.mo.gov/cnet/cases/charges.do"
    DOCKETS_URL = "https://www.courts.mo.gov/cnet/cases/docketEntriesSearch.do"
    SERVICE_URL = "https://www.courts.mo.gov/casenet/cases/service.do"

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
            retries = Retry(total=0, backoff_factor=5)

            self._GLOBAL_SESSION.mount(
                "http://", HTTPAdapter(max_retries=retries)
            )
            self._GLOBAL_SESSION.mount(
                "https://www.courts.mo.gov",
                HTTPAdapter(max_retries=3),
            )
        return self._GLOBAL_SESSION

    def get_case_details(self, case_number, court_code):
        params = {"caseNumber": case_number, "courtId": court_code}
        response = self.GLOBAL_SESSION.get(
            self.CASE_NO_SEARCH_URL, headers=self.HEADERS, params=params
        )
        results = response.json()
        return results

    def get_case_charges(self, case_number, court_code):
        params = {"caseNumber": case_number, "courtId": court_code}
        response = self.GLOBAL_SESSION.get(
            self.CHARGES_URL, headers=self.HEADERS, params=params
        )
        results = response.json()
        return results

    def get_case_parties(self, case_number, court_code):
        params = {"caseNumber": case_number, "courtId": court_code}
        response = self.GLOBAL_SESSION.get(
            self.PARTIES_URL, headers=self.HEADERS, params=params
        )
        results = response.json()
        return results

    def get_case_dockets(self, case_number, court_code):
        params = {"caseNumber": case_number, "courtId": court_code}
        # params_url = "displayOption=A&sortOption=D&hasChange=false&caseNumber=210331459&courtId=CT16&isTicket="
        params = {
            "displayOption": "A",
            "sortOption": "D",
            "hasChange": "false",
            "caseNumber": case_number,
            "courtId": court_code,
            "isTicket": "",
        }
        response = self.GLOBAL_SESSION.get(
            self.DOCKETS_URL, headers=self.HEADERS, params=params
        )
        results = response.json()
        return results

    def get_docket_file_url(self, filename, docket_court_code, docket_di):
        # https://www.courts.mo.gov/fv/c/210331459_NOTICE+OF+NEW+COURT+DATE_CR400_SMC_2023-Apr-18_FINAL.pdf.pdf?courtCode=16&di=22096259
        params = {"courtCode": docket_court_code, "di": docket_di}
        url_base = self.BASE_URL + f"/fv/c/{filename}"
        url_params = urlencode(params)
        return url_base + "?" + url_params

    def get_case_dockets_details(self, case_details):
        def get_doc_dict(doc):
            if doc.get("document") is not None:
                docket_desc = {"docketDesc": doc.get("docketDesc")}
                doc_dict = doc.get("document")
                doc_dict.update(docket_desc)
                return doc_dict
            else:
                return None

        documents = [
            get_doc_dict(doc) for doc in case_details.get("docketTabModelList")
        ]
        return [doc for doc in documents if doc is not None]

    def get_defendant(self, case_details):
        """
        case_details :
        """

        defendant = {}
        for party in case_details["partyDetailsList"]:
            if party.get("descCode") == "DFT":
                defendant["address_a_type"] = party.get("addrAtyp")
                defendant["address_city"] = party.get("addrCity")
                defendant["address_line_1"] = party.get("addrLine1")
                defendant["address_seq_no"] = party.get("addrSeqNo")
                defendant["address_state_code"] = party.get("addrStatCode")
                defendant["address_zip"] = party.get("addrZip")
                defendant["birth_date"] = party.get("birthDate")
                defendant["birth_date_code"] = party.get("birthDateCode")
                defendant["criminal_case"] = party.get("criminalCase")
                defendant["criminal_ind"] = party.get("criminalInd")
                defendant["description"] = party.get("desc")
                defendant["description_code"] = party.get("descCode")
                defendant["first_name"] = party.get("firstName")
                defendant["year_of_birth"] = party.get("formattedBirthDate")
                defendant["formatted_party_address"] = party.get(
                    "formattedPartyAddress"
                )
                defendant["formatted_party_name"] = party.get(
                    "formattedPartyName"
                )
                defendant["formatted_telephone"] = party.get(
                    "formattedTelePhone"
                )
                defendant["last_name"] = party.get("lastName")
                defendant["lit_ind"] = party.get("litInd")
                defendant["middle_name"] = party.get("midInitial")
                defendant["party_type"] = party.get("partyType")
                defendant["pidm"] = party.get("pidm")
                defendant["pred_code"] = party.get("predCode")
                defendant["prosecuting_atty"] = party.get("prosecutingAtty")
                defendant["pty_seq_no"] = party.get("ptySeqNo")
                defendant["sort_seq"] = party.get("sortSeq")

                defendant["age"] = self.get_age(defendant["birth_date"])
                break

        return defendant

    def get_age(self, birth_date: str):
        """Get age from birth date

        This function returns an integer.
        """
        try:
            today = datetime.date.today()
            birth_date_parsed = datetime.datetime.strptime(
                birth_date, "%m/%d/%Y"
            )
            age = (
                today.year
                - birth_date_parsed.year
                - (
                    (today.month, today.day)
                    < (birth_date_parsed.month, birth_date_parsed.day)
                )
            )
        except Exception as e:
            logger.error(f"Error getting age : {str(e)}")
            age = None
        return age

    def get_case_info(self, case) -> dict:
        """Get every information of case detail by parsing rendered HTML page

        This function returns an object.
        """
        case_detail = {}
        case_number = case["case_number"]
        court_id = case["court_code"]

        # Retrieve the case parties
        try:
            console.print(f"Getting case parties : {case_number}")
            parties = self.get_case_parties(case_number, court_id)
            case_detail.update(parties)
        except Exception as e:
            logger.error(f"Connection failure : {str(e)}")
            console.print(f"Retrieval of case parties failed {case_number}")
        self.sleep()

        # Retrieve the defendant
        case_detail.update(self.get_defendant(case_detail))

        # Retrieve the dockets
        try:
            console.print(f"Getting case dockets : {case_number}")
            dockets = self.get_case_dockets(case_number, court_id)
            case_detail.update(dockets)

        except Exception as e:
            logger.error(f"Connection failure : {str(e)}")
            console.print(f"Retrieval of case dockets failed {case_number}")

        # Get the documents from the docker files
        documents = self.get_case_dockets_details(case_detail)

        # Download the docket files
        parsed_ticket = {}
        for doc in documents:
            docket_file_url = self.get_docket_file_url(
                doc["documentTitle"], court_id, doc["documentId"]
            )
            docket_file_path = self.download(
                docket_file_url, filetype=doc.get("documentExtension", "pdf")
            )
            self.upload_file(docket_file_path)
            if "citation" in doc.get("docketDesc", "").lower():
                docker_image_path = self.convert_to_png(
                    docket_file_path, case_number
                )
                parsed_ticket = self.parse_ticket(
                    docker_image_path, case_number
                )
                self.upload_file(docker_image_path)
                case_detail["ticket"] = parsed_ticket

        return self.t_dict(case_detail)

    def lower_case_dict(self, case):
        """Convert all keys in a dictionary to lowercase

        This function returns a dictionary.
        """
        if not isinstance(case, dict):
            return case
        return dict(
            (k.lower(), self.lower_case_dict(v)) for k, v in case.items()
        )

    def rename_keys(self, case_detail):
        """Rename keys in a dictionary

        This function returns a dictionary.
        """
        rename = {
            "party_detailslist": "parties",
            "docket_tabmodellist": "dockets",
            "case_chargelist": "charges",
            "judge_details": "judge",
            "case_fineamountmodel": "fine",
        }
        return {rename.get(k, k): v for k, v in case_detail.items()}

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

        # Getting extra case details
        case_detail = self.get_case_info(case_info)
        case_detail = self.rename_keys(case_detail)
        # Save the case details in Json file
        self.save_json(case_detail, case_id)

        try:
            # Getting all the details
            case_info["charges_description"] = case_detail.get(
                "charges", [{"charge_description": ""}]
            )[0].get("charge_description", "")

        except Exception as e:
            logger.error(
                f"Failed to retrieve information for case"
                f" from CaseNet "
                f"{case_id} - error {e}"
            )
            raise e
        logger.info(f"Succeeded to get details for case " f"{case_id}")
        console.print(f"Succeeded to get details for case " f"{case_id}")
        return case_info

    def get_cases(
        self,
        court: Court,
        date,
        case_type="Infraction",
        cases_ignore=None,
        limit=10,
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
            '"column":0,"dir":"asc"}],"start":0,'
            '"length":1000,"search":{"value":"",'
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
            cases_to_scrape = cases_to_scrape[:limit]
        except Exception as e:
            logger.error(
                f"Failed to retrieve cases from CaseNet "
                f"for {court.name} - error {e} - url {url}"
            )
            raise e

        def parse_case_wrapper(case):
            with console.status(
                f"[bold green]Scraping case {case.get('caseNumber')} ..."
            ) as status:
                try:
                    output = self.parse_case(case, case_type, court, date)
                    status.update(
                        f"[bold green]Scraped case {case.get('caseNumber')} "
                        f"..."
                    )
                except Exception as e:
                    console.log(
                        f"[bold red]Failed to scrape case "
                        f"{case.get('caseNumber')} - error {e}"
                    )
                    return None
                return output

        results = [parse_case_wrapper(case) for case in cases_to_scrape]
        return [r for r in results if r is not None]


if __name__ == "__main__":
    case = {"case_number": "210555271"}

    print(
        json.dumps(
            ScraperMOCourt().get_case_info(case), indent=4, sort_keys=True
        )
    )
    print("Done running", __file__, ".")

    print("Done running", __file__, ".")
