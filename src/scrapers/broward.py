import os
from playwright.async_api import async_playwright, TimeoutError
import requests
from urllib.parse import urlparse, parse_qs

import pandas as pd
from models.cases import Case
from datetime import date, datetime, time
from tempfile import NamedTemporaryFile
from rich.console import Console
from models.leads import Lead
from src.models.cases import Case
from src.models.leads import Lead
from src.scrapers.base.scraper_base import ScraperBase
from rich.progress import Progress
from urllib.parse import urlparse, parse_qs

import re
import os
from twocaptcha import TwoCaptcha
TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')

console = Console()

class BrowardScraper(ScraperBase):
    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)

    def split_full_name(self, name):
        # Use regular expression to split on space, comma, hyphen, or period.
        # This can be expanded to include other delimiters if required.
        parts = re.split(r'[\s,\-\.]+', name)
        
        # Prepare variables for first, middle, and last names
        first_name = middle_name = last_name = ''

        # The list 'parts' now contains the split name parts.
        # How we assign these parts depends on the number of elements in 'parts'.
        if len(parts) > 2:
            first_name = parts[0]
            middle_name = ' '.join(parts[1:-1])  # All parts except first and last are considered middle names
            last_name = parts[-1]
        elif len(parts) == 2:
            first_name, last_name = parts
        elif len(parts) == 1:
            first_name = parts[0]

        return first_name, middle_name, last_name

    async def get_site_key(self):
        iframe = await self.page.query_selector('iframe[title="reCAPTCHA"]')
        
        # Extract the `src` attribute from the iframe
        iframe_src = await iframe.get_attribute('src')
        
        # Close the browser

        parsed_url = urlparse(iframe_src)
        query_params = parse_qs(parsed_url.query)
    
        site_key = query_params.get('k', [None])[0]
        return site_key
    
    async def init_browser(self, case_id):
        console.log("Initation of Browser...")
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(headless=False)
        context = await self.browser.new_context()
        self.page = await context.new_page()
        self.url = "https://www.browardclerk.org/Web2"
        await self.page.goto(self.url)
        await self.page.click("a:has-text('Case Number')")
        case_number_element = await self.page.query_selector('#CaseNumber')
        await case_number_element.fill(f"{case_id}")

        recaptcha_element = await self.page.query_selector('#RecaptchaField3')
        if recaptcha_element:
            site_key = await self.get_site_key()
            response = self.solver.recaptcha(
                sitekey=site_key,
                url=self.url
            )
            code = response['code']
            response_textarea = await recaptcha_element.query_selector('#g-recaptcha-response-2')
            if response_textarea:
                await response_textarea.evaluate('el => el.value = "{}"'.format(code))
            else:
                print("The 'g-recaptcha-response' textarea was not found.")

            submit_button = await self.page.query_selector('#CaseNumberSearchResults')
            if submit_button:
                await submit_button.click()
            else:
                print("The 'submit' button was not found.")
    
    async def detail_search(self, case_id):
        await self.page.wait_for_selector('a:has-text("24001500TI10A")')
        await self.page.click(f'a:has-text("{case_id}")')
        await self.page.wait_for_load_state('load')
        
        filing_date_element = await self.page.query_selector('span:has-text("Filing Date:") + span')
        filing_date = await filing_date_element.inner_text()
        filing_date= datetime.strptime(filing_date, "%m/%d/%Y")

        td_elements = await self.page.query_selector_all('td')
        # Get the name
        name_element = await self.page.query_selector('td b')
        name = await name_element.inner_text()
        name = name.strip()
        first_name, middle_name, last_name = self.split_full_name(name)
        
        # Get the gender
        gender_element = await self.page.query_selector('td >> text="Gender:"')
        gender = await gender_element.evaluate('(element) => element.nextSibling.nodeValue.trim()')
        
        # Get the DOB
        dob_element = await self.page.query_selector('td >> text="DOB:"')
        dob = await dob_element.evaluate('(element) => element.nextSibling.nodeValue.trim()')
        date_components = dob.split("/")
        birth_date = f"{date_components[0]}/{date_components[1]}"
        year_of_birth = date_components[2]
        
        address = await self.page.evaluate('''() => {
            // Find the table cell containing "Defendant"
            const defendantCell = Array.from(document.querySelectorAll('td'))
                .find(td => td.textContent.trim() === 'Defendant');
            
            if (defendantCell) {
                // Locate the parent row <tr> of the cell
                const row = defendantCell.closest('tr');
                // Get the third <td> cell in the row (index 2)
                const bsfCell = row.querySelectorAll('td')[2];
                if (bsfCell) {
                    // Return the text content of the third cell
                    return bsfCell.textContent.trim();
                }
            }
            return null;  // Return null if not found
        }''')
        
        offense_date = await self.page.evaluate('''() => {
            // Find all <tr> elements containing the table rows
            const rows = Array.from(document.querySelectorAll('tr'));
            for (let row of rows) {
                // Check if the row contains "Date Filed:"
                if (row.innerText.includes('Date Filed:')) {
                    // Locate the first <td> with width "100px" in the same row
                    const cells = Array.from(row.querySelectorAll('td'));
                    for (let cell of cells) {
                        if (cell.getAttribute('width') === '100px') {
                            return cell.textContent.trim();
                        }
                    }
                }
            }
            return null;  // Return null if not found
        }''')
        offense_date= datetime.strptime(offense_date, "%m/%d/%Y")
        courts = {}
        court_code = "FL_BROWARD"
        if court_code not in courts.keys():
            courts[court_code] = {
                "code": court_code,
                "county_code": "broward",
                "enabled": True,
                "name": "Florida, broward",
                "state": "FL",
                "type": "CT",
            }
            self.insert_court(courts[court_code])

        case_dict = {
                "case_id": case_id,
                "court_id": court_code,
                "address": address,
                "filing_date": filing_date,
                "offense_date": offense_date,
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
                "gender": gender,
                "birth_date": birth_date,
                "year_of_birth": year_of_birth,
            }
        print(case_dict)
        return case_dict

    async def scrape(self, search_parameters):
        case_id = search_parameters['case_id']
        await self.init_browser(case_id)  
        case_dict = await self.detail_search(case_id)  
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
                case = Case(**case_dict)
                lead = Lead(**case_dict)
                self.insert_case(case)
                self.insert_lead(lead)

            progress.update(task, advance=1)
       
        await self.browser.close()