import datetime
import json
import logging
import traceback
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from requests.adapters import HTTPAdapter, Retry
from rich.console import Console

from src.components.cases.events import get_case_events
from src.core.config import get_settings
from src.models.courts import Court
from src.scrapers.base import InitializedSession, ScraperBase

settings = get_settings()

logger = logging.Logger(__name__)

console = Console()


class ScraperMOCourt(ScraperBase):
    """MO Court scraper"""

    BASE_URL = "https://www.courts.mo.gov"
    HEADERS = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": "JSESSIONID=0001xDx5JIZm3DwDRLRsNTSZOAn:-22P55D; UJID=540e1b6b-483b-40a1-8029-0d1d2bb6387f; visitorid=20230506105547481548; visid_incap_1276241=Ge/9RPYCQoGPMRvbDa2n/iUNgmQAAAAAQUIPAAAAAAC5YNLDDGM2kQoI+XusVdVM; _ga=GA1.1.1638297028.1690574877; _ga_DSVJ8DTRVZ=GS1.1.1690574876.1.1.1690574891.0.0.0; JSESSIONID=0001LDEnCXeHAbauBaVxQhpgwkQ:-850S3K; visid_incap_1276232=snCAyo/HSmmVP1XiFEiDad50J2YAAAAAQUIPAAAAAAAp26aC3CQomBOjHrXXJ7FW; incap_ses_1776_1276232=hVovX/MIbh0/sWbMm56lGN50J2YAAAAAgDNKdw0dz3OYTCqHNpBmnA==; UJIA=-1179896343; UJIA=-1807178282; UJID=540e1b6b-483b-40a1-8029-0d1d2bb6387f",
        "DNT": "1",
        "Origin": "https://www.courts.mo.gov",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }
    CASE_NO_SEARCH_URL = (
        "https://www.courts.mo.gov/cnet/cases/newHeaderData.do"
    )
    PARTIES_URL = "https://www.courts.mo.gov/cnet/cases/party.do"
    CHARGES_URL = "https://www.courts.mo.gov/cnet/cases/charges.do"
    DOCKETS_URL = "https://www.courts.mo.gov/cnet/cases/docketEntriesSearch.do"
    SERVICE_URL = "https://www.courts.mo.gov/casenet/cases/service.do"
    EVENT_URL = "https://www.courts.mo.gov/cnet/cases/event.do"

    def get_referer(self, case_number, court_code):
        return f"https://www.courts.mo.gov/cnet/cases/newHeader.do?inputVO.caseNumber={case_number}&inputVO.courtId={court_code}&inputVO.isTicket=false"

    @property
    def GLOBAL_SESSION(self):
        if self._GLOBAL_SESSION is None:
            url = "https://www.courts.mo.gov/cnet/login"

            payload = f"backUrl=%2Fwelcome.do&username={self.username}&password={self.password}&logon=logon"
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": "JSESSIONID=00015UfAySwtWC_Nyvt3Gi08y89:-22P55D; UJID=540e1b6b-483b-40a1-8029-0d1d2bb6387f; visitorid=20230506105547481548; visid_incap_1276241=Ge/9RPYCQoGPMRvbDa2n/iUNgmQAAAAAQUIPAAAAAAC5YNLDDGM2kQoI+XusVdVM; _ga=GA1.1.1638297028.1690574877; _ga_DSVJ8DTRVZ=GS1.1.1690574876.1.1.1690574891.0.0.0; JSESSIONID=0001LDEnCXeHAbauBaVxQhpgwkQ:-850S3K; visid_incap_1276232=snCAyo/HSmmVP1XiFEiDad50J2YAAAAAQUIPAAAAAAAp26aC3CQomBOjHrXXJ7FW; incap_ses_1776_1276232=hVovX/MIbh0/sWbMm56lGN50J2YAAAAAgDNKdw0dz3OYTCqHNpBmnA==; UJIA=-1179896343; UJIA=-1807178282; UJID=540e1b6b-483b-40a1-8029-0d1d2bb6387f",
                "DNT": "1",
                "Origin": "https://www.courts.mo.gov",
                "Pragma": "no-cache",
                "Referer": "https://www.courts.mo.gov/cnet/logon.do?backUrl=/welcome.do",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "sec-ch-ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
            }

            self._GLOBAL_SESSION = InitializedSession()
            response = self._GLOBAL_SESSION.request(
                "POST", url, headers=headers, data=payload
            )
            # TODO: #13 Should login at the beginning !
            retries = Retry(total=0, backoff_factor=5)

            self._GLOBAL_SESSION.mount(
                "http://", HTTPAdapter(max_retries=retries)
            )
            self._GLOBAL_SESSION.mount(
                "https://www.courts.mo.gov",
                HTTPAdapter(max_retries=3),
            )
        return self._GLOBAL_SESSION

    def search_case(self, case_id):
        payload = f"courtType=&countyCode=&cortCode=SW&caseNumber={case_id}"
        cookies = self.GLOBAL_SESSION.cookies.get_dict()
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": cookie_str,
            "DNT": "1",
            "Origin": "https://www.courts.mo.gov",
            "Pragma": "no-cache",
            "Referer": "https://www.courts.mo.gov/cnet/caseNoSearch.do",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not=A?Brand";v="99", "Chromium";v="118"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
        }

        url = "https://www.courts.mo.gov/cnet/caseNoSearch.do"

        response = self.GLOBAL_SESSION.post(
            url,
            headers=headers,
            data=payload,
        )

        # Parse the new URL https://www.courts.mo.gov/cnet/cases/newHeader.do?inputVO.caseNumber=704195410&inputVO.courtId=SMPDB0005_CT25&inputVO.isTicket=false
        url_parsed = urlparse(response.url)

        query_params = dict(parse_qs(url_parsed.query))

        return {
            "case_number": query_params.get("inputVO.caseNumber", [None])[0],
            "court_code": query_params.get("inputVO.courtId", [None])[0],
        }

    def get_case_details(self, case_number, court_code):
        params = {"caseNumber": case_number, "courtId": court_code}
        params_parsed = urlencode(params)
        response = self.GLOBAL_SESSION.post(
            self.CASE_NO_SEARCH_URL, headers=self.HEADERS, data=params_parsed
        )
        results = response.json()
        return results

    def get_case_charges(self, case_number, court_code):
        params = {"caseNumber": case_number, "courtId": court_code}
        params_parsed = urlencode(params)
        response = self.GLOBAL_SESSION.post(
            self.CHARGES_URL, headers=self.HEADERS, data=params_parsed
        )
        results = response.json()
        return results

    def get_case_parties(self, case_number, court_code):
        params = {"caseNumber": case_number, "courtId": court_code}
        params_parsed = urlencode(params)
        self.HEADERS["Referer"] = self.get_referer(case_number, court_code)
        response = self.GLOBAL_SESSION.post(
            self.PARTIES_URL, headers=self.HEADERS, data=params_parsed
        )
        results = response.json()
        return results

    def get_case_events(self, case_number, court_code):
        params = {
            "inputVO.caseNumber": case_number,
            "inputVO.courtId": court_code,
        }
        payload = '{"draw":1,"columns":[{"data":"formattedScheduledDate","name":"","searchable":true,"orderable":true,"search":{"value":"","regex":false}},{"data":"caseNumber","name":"","searchable":true,"orderable":true,"search":{"value":"","regex":false}}],"order":[{"column":0,"dir":"asc"}],"start":0,"length":10,"search":{"value":"","regex":false}}'

        cookies = self.GLOBAL_SESSION.cookies.get_dict()
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/json;charset=UTF-8",
            "Cookie": cookie_str,
            "DNT": "1",
            "Origin": "https://www.courts.mo.gov",
            "Pragma": "no-cache",
            "Referer": f"https://www.courts.mo.gov/cnet/cases/newHeader.do?inputVO.caseNumber={case_number}&inputVO.courtId={court_code}&inputVO.isTicket=false",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
        }

        response = self.GLOBAL_SESSION.post(
            self.EVENT_URL, headers=headers, params=params, data=payload
        )
        results = response.json().get("data")
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
        params_parsed = urlencode(params)
        response = self.GLOBAL_SESSION.post(
            self.DOCKETS_URL, headers=self.HEADERS, data=params_parsed
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
            if doc.get("document") is not None and doc.get("document", []):
                docket_desc = {"docketDesc": doc.get("docketDesc")}
                if len(doc.get("document")) > 1:
                    console.log(
                        f"More than one document found for docket {doc.get('docketDesc')}"
                    )
                doc_dict = doc.get("document").pop()
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
        court_id = case.get("court_code", None)

        if court_id is None:
            court_id = self.search_case(case_number)["court_code"]

        # Retrieve the case parties
        try:
            console.print(f"Getting case parties : {case_number}")
            parties = self.get_case_parties(case_number, court_id)
            case_detail.update(parties)
        except Exception as e:
            logger.error(f"Connection failure : {str(e)}")
            console.print(f"Retrieval of case parties failed {case_number}")
        self.sleep()

        if not case_detail:
            logger.error(f"No case details found for {case_number}")
            console.print(f"No case details found for {case_number}")
            raise Exception("No case details found")

        # Retrive the events of the case
        try:
            console.print(f"Getting case events : {case_number}")
            events = self.get_case_events(case_number, court_id)
            case_detail["court_events"] = events
        except Exception as e:
            logger.error(f"Connection failure : {str(e)}")
            console.print(f"Retrieval of case events failed {case_number}")

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

        if not documents:
            logger.error(f"No documents found for {case_number}")
            console.print(f"No documents found for {case_number}")
            # raise Exception("No documents found")

        # Download the docket files
        parsed_ticket = {}
        parsed_documents = []
        for doc in documents:
            docket_file_url = self.get_docket_file_url(
                doc["documentTitle"], court_id, doc["documentId"]
            )
            docket_file_path = self.download(
                docket_file_url, filetype=doc.get("documentExtension", "pdf")
            )
            self.sleep()
            file_path = self.upload_file(docket_file_path)
            doc["file_path"] = file_path
            if "citation" in doc.get("docketDesc", "").lower() and False:
                docker_image_path = self.convert_to_png(
                    docket_file_path, case_number
                )
                parsed_ticket = self.parse_ticket(
                    docker_image_path, case_number
                )
                img_file_path = self.upload_file(docker_image_path)
                case_detail["ticket_img"] = img_file_path
                case_detail["ticket"] = parsed_ticket
            parsed_documents.append(doc)
        case_detail["documents"] = parsed_documents
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
            case_info["case_date"] = case_detail.get("filing_date", "")
            case_info.update(case_detail)
            case_info["court_code"] = court.code

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
                    # Console log with traceback for debugging
                    console.log(
                        f"[bold red]Failed to scrape case "
                        f"{case.get('caseNumber')} - error {e}"
                    )
                    console.log(traceback.format_exc())

                    return None
                return output

        results = [parse_case_wrapper(case) for case in cases_to_scrape]
        return [r for r in results if r is not None]

    def parse_single_case(self, case, case_type, court, date):
        with console.status(
            f"[bold green]Scraping case {case.get('caseNumber')} ..."
        ) as status:
            try:
                output = self.parse_case(case, case_type, court, date)
                status.update(
                    f"[bold green]Scraped case {case.get('caseNumber')} "
                    f"..."
                )
                return output
            except Exception as e:
                # Console log with traceback for debugging
                console.log(
                    f"[bold red]Failed to scrape case "
                    f"{case.get('caseNumber')} - error {e}"
                )
                console.log(traceback.format_exc())

                raise e


if __name__ == "__main__":
    case = {"case_number": "210555271"}

    print(
        json.dumps(
            ScraperMOCourt().get_case_info(case), indent=4, sort_keys=True
        )
    )
    print("Done running", __file__, ".")

    print("Done running", __file__, ".")
