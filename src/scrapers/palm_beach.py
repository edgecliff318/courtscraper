from playwright.async_api import async_playwright, TimeoutError
from urllib.parse import urlparse, parse_qs
from models.cases import Case
from models.leads import Lead
from src.scrapers.base import ScraperBase
from datetime import date, datetime, time
from tempfile import NamedTemporaryFile
from rich.console import Console
from rich.progress import Progress
import requests
import pandas as pd
import re
import os
from twocaptcha import TwoCaptcha

TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')

console = Console()

class PalmBeachScraper(ScraperBase):
    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)

    async def get_next_cell_text(self, page, search_text):
        selector = f"//td[text()='{search_text}']/following-sibling::td"
        return await page.evaluate(f"""(selector) => {{
            const cell = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            return cell ? cell.textContent.trim() : '';
        }}""", selector)
        
    async def init_browser(self):
        console.log("Initation of Browser...")
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(headless=False)
        context = await self.browser.new_context()
        self.page = await context.new_page()
        self.url = "https://appsgp.mypalmbeachclerk.com/eCaseView/landingpage.aspx"
        await self.page.goto(self.url)
        guest_element = await self.page.query_selector("#cphBody_ibGuest")
        if guest_element:
            await guest_element.click()
        else:
            print("The 'guest' button was not found.")

    async def get_courts(self):
        console.log("Getting courts...")
        court_names = await self.page.query_selector_all("input[name='courtName']")
        court_ids = await self.page.query_selector_all("input[name='courtFips']")
        print(f"court ids-{court_names}")
        print(f"court ids-{court_ids}")
        courts = []
        for court_id, court_name in zip(court_ids, court_names):
            court = {
                "court_id": await court_id.get_attribute("value"),
                "court_desc": await court_name.get_attribute("value")
            }
            courts.append(court)

        return courts

    async def search_by_case_number(self,court_types, offense_begin_date):
        await self.page.wait_for_load_state('networkidle')  # Wait until network is idle
        recaptcha_element = await self.page.query_selector('div.g-recaptcha')
        if recaptcha_element:
            site_key = await recaptcha_element.get_attribute('data-sitekey')
            response = self.solver.recaptcha(
                sitekey=site_key,
                url=self.url
            )
            code = response['code']
            response_textarea = await recaptcha_element.query_selector('textarea#g-recaptcha-response')

            if response_textarea:
                await response_textarea.evaluate('el => el.value = "{}"'.format(code))
            else:
                print("The 'g-recaptcha-response' textarea was not found.")
            submit_button = await self.page.query_selector('input#cphBody_cmdContinue')
            if submit_button:
                await submit_button.click()
            else:
                print("The 'submit' button was not found.")
            await self.page.select_option('#cphBody_gvSearch_cmbParameterPostBack_5', label=f"{court_types}")
            await self.page.fill("#cphBody_gvSearch_txtParameter_8", f'{offense_begin_date}')

            search_button = await self.page.query_selector("#cphBody_cmdSearch")
            if search_button:
                await search_button.click()
            else:
                print("The 'search' button was not found.")

    async def detail_search(self, order):
        case_id = await self.page.inner_text(f'#cphBody_gvResults_lbCaseNumber_{order}')
        court_id = case_id.split('-')[0]
        await self.page.click(f'#cphBody_gvResults_lbCaseNumber_{order}', timeout = 6000)
        first_name = await self.get_next_cell_text(self.page, "First Name")
        middle_name =  await self.get_next_cell_text(self.page, "Middle Name")
        last_name =  await self.get_next_cell_text(self.page, "Last Name")
        date_parts = (await self.get_next_cell_text(self.page, "DOB")).split('/')
        if date_parts != ['']:
            birth_date = f"{date_parts[0]}/{date_parts[1]}" 
            year_of_birth = date_parts[2]
        else:
            birth_date = ""
            year_of_birth = ""
        filing_date =  await self.get_next_cell_text(self.page, "Filing Date")
        offense_date =  await self.get_next_cell_text(self.page, "Offense Date")
        case_dict = {
                        "case_id": case_id,
                        "court_id": court_id,
                        "first_name": first_name,
                        "middle_name": middle_name,
                        "last_name": last_name,
                        "year_of_birth": year_of_birth,
                        "birth_date": birth_date,
                        "filing_date": filing_date,
                        "offense_date": offense_date,
                    }
        with Progress() as progress:
            task = progress.add_task(
                "[red]Inserting cases...", total=len(case_dict)
            )
            
            case_id = case_dict.get("case_id")
            if self.check_if_exists(case_id):
                console.log(
                    f"Case {case_id} already exists. Skipping..."
                )
                progress.update(task, advance=1)
            else:
                self.insert_case(case_dict)
                self.insert_lead(case_dict)

            progress.update(task, advance=1)
        
        return case_dict
    
    async def scrape(self, search_parameter):
        court_types = search_parameter["court_types"]
        offense_begin_date = search_parameter["offense_begin_date"]
        await self.init_browser()
        await self.search_by_case_number(court_types, offense_begin_date)
        order = 0
        while True:
            try:
                case_dict = await self.detail_search(order)
                order = order+1
                await self.page.evaluate('window.history.back()')
                print(case_dict)
            except TimeoutError as e:
                print()
                break
        await self.browser.close()