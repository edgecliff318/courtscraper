""" Scraper for FL Palm Beach County Court """

import re
import os
import requests
import pandas as pdx

from playwright.async_api import async_playwright, TimeoutError
from urllib.parse import urlparse, parse_qs
from datetime import date, datetime, time,  timedelta
from tempfile import NamedTemporaryFile
from rich.console import Console
from rich.progress import Progress

from src.models.cases import Case
from src.models.leads import Lead
from src.scrapers.base import ScraperBase

from twocaptcha import TwoCaptcha

TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')

console = Console()

class FLPalmBeachScraper(ScraperBase):
    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)

    def increase_date_by_one_day(self, date_str):
        """Increase the given date string by one day."""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        new_date_obj = date_obj + timedelta(days=1)
        return new_date_obj.strftime("%Y-%m-%d")
    
    async def get_next_cell_text(self, page, search_text):
        selector = f"//td[text()='{search_text}']/following-sibling::td"
        return await page.evaluate(f"""(selector) => {{
            const cell = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            return cell ? cell.textContent.trim() : '';
        }}""", selector)
        
    async def init_browser(self):
        console.log("Initation of Browser...")
        pw = await async_playwright().start()    
            
        # Proxy 9090
        self.browser = await pw.chromium.launch(
            headless=True,
            # args=["--proxy-server=socks5://localhost:9090"]
        )

        context = await self.browser.new_context()
        self.page = await context.new_page()
        self.url = "https://appsgp.mypalmbeachclerk.com/eCaseView/landingpage.aspx"
        
        await self.page.goto(self.url)
        await self.wait_for_page_load()
        
        guest_element = await self.page.query_selector("#cphBody_ibGuest")
        if guest_element:
            await guest_element.click()
        else:
            print("The 'guest' button was not found. Quiting...")
            await self.browser.close()

    async def resolve_captcha(self, recaptcha_element):
        """
        resolve_captcha will take captcha element
        and find site key then solve and submit captcha
        """
        site_key = await recaptcha_element.get_attribute("data-sitekey")
        response = self.solver.recaptcha(sitekey=site_key, url=self.url)
        code = response["code"]
        response_textarea = await recaptcha_element.query_selector(
            "textarea#g-recaptcha-response"
        )

        if response_textarea:
            await response_textarea.evaluate('el => el.value = "{}"'.format(code))
        else:
            print("The 'g-recaptcha-response' textarea was not found.")
        submit_button = await self.page.query_selector("input#cphBody_cmdContinue")
        if submit_button:
            await submit_button.click()
        else:
            print("The 'submit' button was not found.")
        print("Captcha Resolved")

    async def find_solve_captcha(self):
        """
        find_solve_captcha will call resolve_captcha if found
        """
        try:
            # resolve captcha if found
            recaptcha_element = await self.page.query_selector("div.g-recaptcha")
        except Exception as _:
            print("No Captcha Element")
            recaptcha_element = False

        if recaptcha_element:
            print("Resolving Captcha")
            await self.resolve_captcha(recaptcha_element)
            await self.wait_for_page_load()
        else:
            print("Captcha Not Found!")

    async def wait_for_page_load(self):
        """
        waiting for page and dom loading
        """
        try:
            await self.page.wait_for_load_state(
                "networkidle"
            )  # Wait until network is idle
        except Exception as _:
            await self.page.wait_for_load_state(
                "domcontentloaded"
            )  # Wait until network is idle

    async def get_charges(self):
        """
        get_charges will switch section and find charges
        then switch back to original section.
        """
        await self.page.click(
            "//a[@title='Charges / Sentences'][contains(@class,'nav-link')]"
        )
        await self.page.wait_for_load_state("networkidle")
        charges = await self.page.locator(
            "//tr[@class='dataheader']/following-sibling::tr/td[3]"
        ).evaluate_all("(elements) => elements.map(el => el.textContent)")
        return [{"description": item} for item in charges]

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
        """
        search_by_case_number will wait for page load
        call find_solve_captcha to solve captcha if any
        then fill data and click search
        """
        # await page load
        await self.wait_for_page_load()

        # check solve captcha
        await self.find_solve_captcha()

        # enter search case detail
        await self.page.select_option(
            "#cphBody_gvSearch_cmbParameterPostBack_5", label=f"{court_types}"
        )
        await self.page.fill(
            "#cphBody_gvSearch_txtParameter_8", f"{offense_begin_date}"
        )

        search_button = await self.page.query_selector("#cphBody_cmdSearch")
        if search_button:
            await search_button.click()
            # await page load
            await self.wait_for_page_load()
        else:
            print("The 'search' button was not found.")

    async def detail_search(self, order):
        """
        detail_search will wait for page content and dom load
        open case using order var then collect case data
        """
        # await page load
        await self.wait_for_page_load()

        case_id = await self.page.inner_text(f'#cphBody_gvResults_lbCaseNumber_{order}')
        court_id = case_id.split('-')[0]
        await self.page.click(f'#cphBody_gvResults_lbCaseNumber_{order}', timeout = 6000)

        # await page load
        await self.wait_for_page_load()

        # check solve captcha
        await self.find_solve_captcha()

        first_name = await self.get_next_cell_text(self.page, "First Name")
        middle_name =  await self.get_next_cell_text(self.page, "Middle Name")
        last_name =  await self.get_next_cell_text(self.page, "Last Name")

        status = "new"  # The status should be always new
        state = "FL"
        race = await self.get_next_cell_text(self.page, "Race")
        sex = await self.get_next_cell_text(self.page, "Sex")

        date_parts = (await self.get_next_cell_text(self.page, "DOB")).split('/')
        if date_parts != ['']:
            birth_date = f"{date_parts[0]}/{date_parts[1]}" 
            year_of_birth = date_parts[2]
        else:
            birth_date = ""
            year_of_birth = ""
        filing_date =  await self.get_next_cell_text(self.page, "Filing Date")
        filing_date = (
            datetime.strptime(filing_date, "%m/%d/%Y").date().strftime("%Y-%m-%d")
            if filing_date
            else ""
        )
        offense_date =  await self.get_next_cell_text(self.page, "Offense Date")

        # fetch charges by changing section
        charges = await self.get_charges()
        await self.page.evaluate("window.history.back()")
        print("Went Back...")

        await self.page.click("//a[@title='Party Names'][contains(@class,'nav-link')]")
        await self.page.wait_for_load_state("networkidle")
        await self.page.evaluate("window.history.back()")
        print("Went Back...")

        case_dict = {
            "case_id": case_id,
            "court_id": court_id,
            "court_code": court_id,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "status": status,
            "state": state,
            "race": race,
            "sex": sex,
            "birth_date": birth_date,
            "year_of_birth": year_of_birth,
            "filing_date": filing_date,
            "case_date": filing_date,
            "offense_date": offense_date,
            "charges": charges,
            "charges_description": " ".join([item["description"] for item in charges]),
            "address_line_1": "",
            "address_city": "",
            "address_state_code": "",
            "address_zip": "",
            "address": "",
            "city": "",
            "zip_code": "",
            "county": "Palm Beach county",
            "source": "Florida State, Palm Beach county",
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
    
    async def scrape(self):
        # to track records to skip duplicates
        already_processed = []
        retry_counter = 0
        await self.init_browser()
        retry_counter += 1

        court_types = "Criminal Traffic"
        last_offense_begin_date = self.state.get("last_offense_begin_date", "2024-07-10")
        offense_begin_date = last_offense_begin_date
        not_found_count = 0
        while True:
            try:
                if not_found_count > 10:
                    console.log(
                        "Too many filing dates not found. Ending the search."
                    )
                    break
                
                last_offense_begin_date = self.increase_date_by_one_day(last_offense_begin_date)
                offense_begin_date = last_offense_begin_date

                self.state["last_offense_begin_date"] = last_offense_begin_date
                # self.update_state()
                await self.search_by_case_number(court_types, offense_begin_date)

                # await page load
                await self.wait_for_page_load()

                records_per_page = 50
                # calculate total pages on basis of records per page
                total_pages_count = int(200 / records_per_page)
                try:
                    # select per page records
                    await self.page.locator("#cphBody_cmbPageSize").select_option(
                        f"{records_per_page}"
                    )
                except Exception as _:
                    print("Failed to find and select all results. Exiting...")
                    return False

                page_no = 1

                while True:
                    # loop to traverse pagination
                    print(f"Processing Page No:\t{page_no}")
                    order = 0
                    while order < records_per_page:
                        # loop to traverse cases
                        page_order = (page_no, order)
                        if page_order in already_processed:
                            print(f"Already Processed:\t{page_order}")
                            order += 1
                            continue

                        print(f"Processing:\t{page_order}")
                        case_dict = await self.detail_search(order)

                        if not case_dict:
                            console.log(
                                f"Case not found. Skipping ..."
                            )
                            not_found_count += 1
                            continue

                        not_found_count = 0

                        if case_dict:       
                            case_id = case_dict["case_id"]
                            if self.check_if_exists(case_id):
                                console.log(
                                    f"Case {case_id} already exists. Skipping..."
                                )
                                continue
                        
                            console.log(f"Inserting case {case_id}...")
                            self.insert_case(case_dict)
                            console.log(f"Inserted case for {case_id})")
                            self.insert_lead(case_dict)
                            console.log(f"Inserted lead for {case_id}")

                        print(f"Order No:\t{order+1}")
                        order += 1
                        await self.page.evaluate("window.history.back()")
                        print("Went Back...")

                        # await page load
                        await self.wait_for_page_load()

                        already_processed.append(page_order)
                        print("Added to already processed...")

                        if len(already_processed) / 100 == 1:
                            # if 100 records collected restart because we face captcha always
                            await self.browser.close()
                            # so we need to quit from two while loops order and page no
                            order = float("inf")
                            print("Set order To: INF")
                            page_no = float("inf")
                            print("Set page_no To: INF")
                            # this will break both while conditions

                    # page while loop break condition
                    page_no += 1
                    if page_no <= total_pages_count:
                        # find next page element
                        await self.page.locator(f"//tr/td/a[text()={page_no}]").click()
                        # await page load
                        await self.wait_for_page_load()
                        # check solve captcha
                        await self.find_solve_captcha()
                    else:
                        # break when page reaches last page
                        break

            except Exception as e:
                console.log(f"Failed while scraping - {e}")
                continue
        await self.browser.close()