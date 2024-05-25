import sys
sys.path.append("..")

from playwright.async_api import async_playwright, TimeoutError
import requests
from urllib.parse import urlparse, parse_qs

import pandas as pd
from models.cases import Case
from src.scrapers.base.scraper_base import ScraperBase
from datetime import date, datetime, time
from tempfile import NamedTemporaryFile
from rich.console import Console
from models.leads import Lead
from rich.progress import Progress

import re
import os
from dotenv import load_dotenv
from twocaptcha import TwoCaptcha
load_dotenv(dotenv_path='.env')
TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')

console = Console()

class WestVirginiaScraper(ScraperBase):
    
    def to_datetime(self, date_str):
        if date_str is None:
            return None
        else:
            return datetime.strptime(date_str, '%m/%d/%Y')
    
    async def init_browser(self):
        console.log("Initation of Browser...")
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        self.url = "https://eapps.courts.state.va.us/ocis/landing"
        await self.page.goto(self.url)

        await self.page.wait_for_timeout(2000)
        accept_button = await self.page.query_selector('#acceptTerms')
        if accept_button:
            await accept_button.click()
        else:
            print("The 'Accept' button was not found.")
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(2000)
        
    
    async def search_by_name(self, search_parameter):
        cookies = await self.context.cookies()
        self.req_cookies = {cookie['name']: cookie['value'] for cookie in cookies} # type:ignore

        console.log(f"self.req_cookies------------{self.req_cookies}")
        url = "https://eapps.courts.state.va.us/ocis-rest/api/public/search"
        data = {"courtLevels":[],"divisions":["Adult Criminal/Traffic"],"selectedCourts":[],"searchString":[f"{search_parameter}"],"searchBy":"N"}
        res = requests.post(url, json=data, cookies=self.req_cookies)
        res_dict = res.json()
        search_result = res_dict['context']['entity']['payload']['searchResults'] 
        return search_result

    def get_case_detail(self, search_result):
        url = "https://eapps.courts.state.va.us/ocis-rest/api/public/getCaseDetails"
        data = search_result
        res = requests.post(url, json=data, cookies=self.req_cookies)
                
        detail_data = res.json()
        case_id = detail_data["context"]["entity"]["payload"]["caseTrackingID"]

        charges = []
        charge = {}
        case_charge = detail_data["context"]["entity"]["payload"]["caseCharge"]

        filing_date = case_charge["chargeFilingDate"]
        offense_date = case_charge["offenseDate"]
        arrest_date = case_charge.get("arrestDate")
        charge["offense_date"] =self.to_datetime(offense_date) #type: ignore
        charge["filing_date"] = self.to_datetime(filing_date) #type: ignore
        charge["arrest_date"] = self.to_datetime(arrest_date) #type: ignore
        charges.append(charge)
        
        
        caseCourt = detail_data["context"]["entity"]["payload"]["caseCourt"]
        court_id = caseCourt["fipsCode"]+caseCourt["courtCategoryCode"]["value"]
        
        caseParticipant = detail_data["context"]["entity"]["payload"]["caseParticipant"]
        for participant in caseParticipant:
            if participant["participantCode"] == "DEF":
                contact_info = participant["contactInformation"]
                last_name = contact_info["personName"].get("personSurName")
                first_name = contact_info["personName"].get("personGivenName")
                middle_name = contact_info["personName"].get("personMiddleName")
                address_city  = contact_info["primaryAddress"].get("locationCityName")
                address_zip = contact_info["primaryAddress"].get("locationState")
                address_state_code = contact_info["primaryAddress"].get("locationPostalCode")
                gender = participant["personalDetails"]["gender"]
                birth_date = participant["personalDetails"].get("maskedBirthDate")
        case_dict = {
                "case_id": case_id,
                "court_id": court_id,
                "charges": charges,
                "filing_date": filing_date,
                "arrest_date": arrest_date,
                "offense_date": offense_date,
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
                "gender": gender,
                "birth_date": birth_date,
                "address_city": address_city,
                "address_zip": address_zip,
                "address_state_code": address_state_code
            }
        return case_dict

    async def scrape(self, search_parameter):
        search_name = search_parameter['name']
        await self.init_browser()
        search_results = await self.search_by_name(search_name)        
        case_dicts = []
        for result in search_results:
            case_dict = self.get_case_detail(result)
            case_dicts.append(case_dict)

        with Progress() as progress:
            task = progress.add_task(
                "[red]Inserting cases...", total=len(case_dicts)
            )
            for case_dict in case_dicts:
                case_id = case_dict.get("case_id")
                if self.check_if_exists(case_id):
                    console.log(
                        f"Case {case_id} already exists. Skipping..."
                    )
                    progress.update(task, advance=1)
                    continue
                self.insert_case(case_dict)
                self.insert_lead(case_dict)

                progress.update(task, advance=1)

        await self.browser.close()