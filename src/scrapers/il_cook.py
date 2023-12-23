import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
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


class IlCook(ScraperBase):
    
    BASE_URL = "https://cccportal.cookcountyclerkofcourt.org/CCCPortal/"
    SEARCH_RESULT_URL = (
        "https://cccportal.cookcountyclerkofcourt.org/app/RegisterOfActionsService/"
    )
    
    def __init__(self, email: str, password: str, url: str):
        self.email = email
        self.password = password
        self.url = url
        self.events = [
            "CombinedEvents",
            "PartyNames",
            "Parties",
            "FinancialSummary",
            "Charges",
            "CaseSummariesSlim",
        ]
        #TODO change the values
        self.start_date = "08/01/2021"
        self.end_date = "12/11/2021"
        self.search_location = "Traffic"
        self.search_hearing_type = "All Traffic Hearing Types"
        self.search_by = "Judicial Officer"
        self.search_judicial_officer = "Aguilar, Carmen Kathleen"


    def _get_id(self, url_path):
        query_params = parse_qs(urlparse(url_path).query)
        return query_params.get("id", [None])[0]
    
    async def get_case_details(self, page, url:str)-> dict:
        id = self._get_id(url)
        response = {}
        for event in self.events:
            data_json = await self.event_to_json(page, event, id)
            response[event] = data_json
        case_details =  await self.parse_case_detail(response)
        print(case_details)
        return case_details    
        

    async def main(self):
        async with async_playwright() as pw:
            print("Connecting...")
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            await self._login(page)
            print("Login successful")
            await self._go_to_table(page)
            print("Table loaded")
            cases_list = await self.get_cases(page)
            print("List of cases downloaded")
            
            for case in cases_list:
                await self.get_case_details(page, case.get("CaseLoadUrl"))
                  


    async def _login(self, page):
        await page.screenshot(path="cases-befor-login.png", full_page=True)

        await page.goto(self.url, timeout=120000)
        await page.click("[id='dropdownMenu1']")
        sign_in_link = await page.query_selector(
            "a[href='/CCCPortal/Account/Login']:has-text('Sign In')"
        )

        if sign_in_link:
            await sign_in_link.click()
        else:
            print("Sign In link not found")

        await page.fill('input[name="UserName"]', self.email)
        await page.fill('input[name="Password"]', self.password)
        login_button = await page.query_selector("button[class='btn btn-primary']")
        if login_button:
            await login_button.click()
        else:
            print("Login button not found")

        await page.wait_for_timeout(2000)
        await page.wait_for_load_state()
        await page.screenshot(path="cases-finish-login.png", full_page=True)

    async def _go_to_table(self, page):
        await page.locator("#portlet-26").click()

        await page.wait_for_timeout(1000)
        await page.wait_for_selector("#cboHSLocationGroup")
        await page.locator("#cboHSLocationGroup").select_option(label="Traffic")
        await page.locator("#cboHSHearingTypeGroup").select_option(
            label="All Traffic Hearing Types"
        )
        await page.locator("#cboHSSearchBy").select_option(label="Judicial Officer")
        await page.locator("#selHSJudicialOfficer").select_option(
            label="Aguilar, Carmen Kathleen"
        )
        await page.fill('input[id="SearchCriteria_DateFrom"]', "08/01/2023")
        await page.fill('input[id="SearchCriteria_DateTo"]', "12/11/2023")
        await page.screenshot(path="select.png")
        await page.locator("#btnHSSubmit").click()
        await page.wait_for_timeout(7000)
        await page.screenshot(path="cases-table.png", full_page=True)

    def _get_id(self, url_path):
        query_params = parse_qs(urlparse(url_path).query)
        id_value = query_params.get("id", [None])[0]
        return id_value

    async def download_case(self, page):
        #TODO change the values 
        document_id = 65756057
        case_num = "YK00073039"
        location_id = 950
        case_id = 24868547
        doc_type_id = 115
        is_version_id = False
        doc_type = "Traffic Document"
        doc_name = "Defendant in Court"
        event_name = "Defendant in Court"

        url = f"https://cccportal.cookcountyclerkofcourt.org/CCCPortal/DocumentViewer/DisplayDoc?documentID={document_id}&caseNum={case_num}&locationId={location_id}&caseId={case_id}&docTypeId={doc_type_id}&isVersionId={is_version_id}&docType={doc_type}&docName={doc_name}&eventName={event_name}"
        response = await page.request.get(url)
        if response.status == 200:
            content = await response.body()
            with open("image.tif", "wb") as file:
                file.write(content)
            print(f"Data saved to {'image.tif'}")
        else:
            print("Failed to fetch data")

    async def event_to_json(self, page, event, id):
        URL = f"https://cccportal.cookcountyclerkofcourt.org/app/RegisterOfActionsService/{event}('{id}')?mode=portalembed"
        if event == "CaseSummariesSlim":
            URL = f"https://cccportal.cookcountyclerkofcourt.org/app/RegisterOfActionsService/{event}?key={id}"
        response = await page.request.get(URL)
        data_json = await response.json()
        print(data_json)
        return data_json

    async def get_cases(self, page):
        url = "https://cccportal.cookcountyclerkofcourt.org/CCCPortal/Hearing/HearingResults/Read"
        payload = {
            "sort": "",  # Update as needed
            "group": "",  # Update as needed
            "filter": "",  # Update as needed
            "portletId": 27,
        }
        response = await page.request.post(url, data=payload)
        data_json = await response.json()
        return data_json.get("Data")

    async def parse_case_detail(self, content: dict) -> dict:
        
        # CaseSummariesSlim
        case_id = content.get("CaseSummariesSlim", {}).get("CaseId")
        court_id = (
            content.get("CaseSummariesSlim", {})
            .get("CaseSummaryHeader", {})
            .get("NodeId")
        )
        court_type = (
            content.get("CaseSummariesSlim", {})
            .get("CaseSummaryHeader", {})
            .get("NodeName")
        )
        judge = (
            content.get("CaseSummariesSlim", {})
            .get("CaseSummaryHeader", {})
            .get("Judge")
        )
        filed_on = (
            content.get("CaseSummariesSlim", {})
            .get("CaseSummaryHeader", {})
            .get("FiledOn")
        )
        case_number = (
            content.get("CaseSummariesSlim", {})
            .get("CaseSummaryHeader", {})
            .get("CaseNumber")
        )
        case_type = (
            content.get("CaseSummariesSlim", {})
            .get("CaseInformation", {})
            .get("CaseType", {})
            .get("Description")
        )
        formatted_party_name = (
            content.get("CaseSummariesSlim", {})
            .get("CaseSummaryHeader", {})
            .get("Style")
        )

        # Parties
        parties = parties = [
            {
                "party_id": party.get("PartyId"),
                "formatted_name": party.get("FormattedName"),
                "last_name": party.get("NameLast"),
                "first_name": party.get("NameFirst"),
                "middle_name": party.get("NameMid"),
                "connection_type": party.get("ConnectionType"),
                "in_jail": party.get("InJail"),
                "race": party.get("Race"),
                "gender": party.get("Gender"),
                "dob": party.get("DateOfBirth"),
                "attorneys": [
                    {
                        "is_lead": attorney.get("IsLead"),
                        "formatted_name": attorney.get("FormattedName"),
                        "address": attorney.get("Addresses")[0]
                        if attorney.get("Addresses")
                        else None,
                    }
                    for attorney in party.get("CasePartyAttorneys", [])
                ],
            }
            for party in content.get("Parties", {}).get("Parties", [])
        ]
        # PartyNames
        first_name = content.get("PartyNames", {}).get("Names", [])[0].get("NameFirst")
        formatted_party_name = (
            content.get("PartyNames", {}).get("Names", [])[0].get("FormattedName")
        )
        last_name = content.get("PartyNames", {}).get("Names", [])[0].get("NameLast")

        # Charges
        charges = [
            {
                "charge_id": charge.get("ChargeId"),
                "party_id": charge.get("PartyId"),
                "case_party_id": charge.get("CasePartyId"),
                "current_charge_num": charge.get("CurrChargeNum"),
                "citation_number": charge.get("CitationNumber"),
                "offense_date": charge.get("OffenseDate"),
                "filed_date": charge.get("FiledDate"),
                "amended_date": charge.get("AmendedDate"),
                "charge_offense": {
                    "jurisdiction": charge.get("ChargeOffense", {}).get("Jurisdiction"),
                    "description": charge.get("ChargeOffense", {}).get(
                        "ChargeOffenseDescription"
                    ),
                    "statute": charge.get("ChargeOffense", {}).get("Statute"),
                    "degree": charge.get("ChargeOffense", {}).get("DegreeDescription"),
                },
                "filing_agency_description": charge.get("FilingAgencyDescription"),
            }
            for charge in content.get("Charges", {}).get("Charges", [])
        ]

        # CombinedEvents
        events = []
        if "Events" in content.get("CombinedEvents", {}):
            for event in content.get("CombinedEvents", {}).get("Events", []):
                event_detail = event.get("Event")
                if event_detail:
                    judge_id_data = event_detail.get("JudgeId", {})
                    judge_id = (
                        judge_id_data.get("Description") if judge_id_data else None
                    )

                    event_data = {
                        "event_id": event.get("EventId"),
                        "event_type": event.get("Type"),
                        "date": event_detail.get("Date"),
                        "judge_id": judge_id,
                        "comment": event_detail.get("Comment"),
                        "criminal_dispositions": [],
                    }

                    criminal_dispositions = event_detail.get("CriminalDispositions", [])
                    for disposition in criminal_dispositions:
                        charge = disposition.get("Charge", {})
                        charge_offense = charge.get("ChargeOffense", {})
                        disposition_data = {
                            "disposition_id": disposition.get(
                                "CriminalDispositionEventId"
                            ),
                            "charge_id": disposition.get("ChargeID"),
                            "disposition_type": disposition.get(
                                "CriminalDispositionTypeId", {}
                            ).get("Description"),
                            "charge": {
                                "charge_id": charge.get("ChargeId"),
                                "description": charge_offense.get(
                                    "ChargeOffenseDescription"
                                ),
                                "degree": charge_offense.get("DegreeId", {}).get(
                                    "Description"
                                ),
                            },
                        }
                        event_data["criminal_dispositions"].append(disposition_data)
                    events.append(event_data)

        return {
            "case_id": case_id,
            "court_id": court_id,
            "court_type": court_type,
            "judge": judge,
            "filed_on": filed_on,
            "case_number": case_number,
            "case_type": case_type,
            "formatted_party_name": formatted_party_name,
            "parties": parties,
            "first_name": first_name,
            "last_name": last_name,
            "charges": charges,
            "events": events,
        }


   


if __name__ == "__main__":
    load_dotenv()
    scraper = IlCook(
        email=os.getenv("EMAIL"),
        password=os.getenv("PASSWORD"),
        url=os.getenv("URL"),
    )
    asyncio.run(scraper.main())
    print("Done running", __file__, ".")
