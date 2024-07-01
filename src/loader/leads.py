import json
import logging
import os

import requests

from src.scrapers.missouri import ScraperMOCourt

logger = logging.getLogger(__name__)


class CaseNet:
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password
        self.session = None

    def login(self):
        if self.session is None:
            self.session = requests.Session()
            url = os.path.join(self.url, "login")
            payload = (
                f"username={self.username}&password="
                f"{self.password}&logon=logon"
            )
            headers = {
                "Connection": "keep-alive",
                "Cache-Control": "max-age=0",
                "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="96", "Google '
                'Chrome";v="96"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "Upgrade-Insecure-Requests": "1",
                "Origin": "https://www.courts.mo.gov",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/96.0.4664.110 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,image/avif,image/webp,"
                "image/apng,*/*;q=0.8,"
                "application/signed-exchange;v=b3;q=0.9",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
                "Sec-Fetch-Dest": "document",
                "Referer": "https://www.courts.mo.gov/cnet/logon.do",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            }

            r = self.session.request(
                "POST", url, headers=headers, data=payload
            )

    def get_cases(
        self, court, date, case_type="Infraction", cases_ignore=None
    ):
        scrapper = ScraperMOCourt(
            url=self.url, username=self.username, password=self.password
        )
        return scrapper.get_cases(
            court=court,
            date=date,
            case_type=case_type,
            cases_ignore=cases_ignore,
        )

    def refresh_case(self, case: dict, parties_only=False):
        scrapper = ScraperMOCourt(
            url=self.url, username=self.username, password=self.password
        )
        case["case_number"] = case.get("case_id")
        case_details = scrapper.get_case_info(case, parties_only=parties_only)
        case_detail = scrapper.rename_keys(case_details)

        charges = case_detail.get("charges", [{"charge_description": ""}])
        if charges:
            case["charges_description"] = charges[0].get(
                "charge_description", ""
            )
        else:
            case["charges_description"] = ""
        case["case_date"] = case_detail.get("filing_date", "")
        case.update(case_detail)
        return case

    def get_single_case(self, case, court, date, case_type="Infraction"):
        scrapper = ScraperMOCourt(
            url=self.url, username=self.username, password=self.password
        )
        return scrapper.parse_single_case(
            case=case, case_type=case_type, court=court, date=date
        )


class LeadsLoader:
    def __init__(self, path: str):
        self.path = path
        self.data = None

    def load(self):
        with open(self.path) as f:
            self.data = json.load(f)
        return self.data

    def save(self, data):
        with open(self.path, "w") as f:
            json.dump(data, f)

    def get_interactions(self, case_number):
        return self.data.get(case_number, {}).get("interactions", [])
