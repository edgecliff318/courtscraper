""" Scraper for Broward County Court """
import asyncio
import re
import os

from playwright.async_api import async_playwright, TimeoutError
from twocaptcha import TwoCaptcha
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from rich.console import Console
from dotenv import load_dotenv

from src.models.cases import Case
from src.models.leads import Lead
from src.scrapers.base.scraper_base import ScraperBase

load_dotenv()
TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')
console = Console()

class BrowardScraper(ScraperBase):
    def __init__(self):
        super().__init__()
        self.solver = TwoCaptcha(TWOCAPTCHA_API_KEY)
        self.courts = {}
        self.browser = None
        self.page = None
        self.url = "https://www.browardclerk.org/Web2"
    
    def split_full_name(self, name):
        # Prepare variables for first, middle, and last names
        first_name = middle_name = last_name = ""

        # Use regular expression to split on space, comma, hyphen, or period.
        parts = re.split(r"[,]+", name)
        if len(parts) > 1:
            last_name = parts[0]

            # Remove the first space from the second part
            second_part = parts[1].lstrip()
            second_part = re.split(r"[\s]+", second_part)

            if len(second_part) > 1:
                first_name = second_part[0]
                middle_name = second_part[1]

            else:
                first_name = second_part[0]

        return first_name, middle_name, last_name

    def parse_full_address(self, full_address):
        pattern = re.compile(
            r'^(?P<address_line_1>[\w\s\#,\.-]+?)[\s,]+'
            r'(?P<address_city>[A-Za-z\s]+?)[\s,]+'
            r'(?P<address_state_code>[A-Z]{2})?[\s,]*'
            r'(?P<address_zip>\d{5}(-\d{4})?|[A-Z0-9 ]{6,10})?$'
        )
        match = pattern.match(full_address.strip())

        if match:
            return (
                match.group('address_line_1').strip() if match.group('address_line_1') else "",
                match.group('address_city').strip() if match.group('address_city') else "",
                match.group('address_state_code').strip() if match.group('address_state_code') else "",
                match.group('address_zip').strip() if match.group('address_zip') else "",
            )
        
        # Fallback parsing for non-matching addresses
        address_line_1, address_city, address_state_code, address_zip = "", "", "", ""
        address_part = re.match(r'^(.*?)[\s,]{2}', full_address)
        city_part = re.search(r',\s*([A-Za-z\s]+)\s*,?\s*[A-Z0-9]*', full_address)
        state_zip_part = re.search(r'([A-Z]{2})?\s*(\d{5}(-\d{4})?|[A-Z0-9 ]{6,10})$', full_address.strip())

        if address_part:
            address_line_1 = address_part.group(1).strip()
        if city_part:
            address_city = city_part.group(1).strip()
        if state_zip_part:
            state_part, zip_part = state_zip_part.group(1), state_zip_part.group(2)
            if state_part:
                address_state_code = state_part.strip()
            if zip_part:
                address_zip = zip_part.strip()

        return address_line_1, address_city, address_state_code, address_zip

    async def get_site_key(self):
        iframe = await self.page.query_selector('iframe[title="reCAPTCHA"]')
        iframe_src = await iframe.get_attribute('src')
        parsed_url = urlparse(iframe_src)
        query_params = parse_qs(parsed_url.query)
        return query_params.get('k', [None])[0]

    async def init_browser(self):
        console.log("Initiating Browser...")
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(headless=False)
        context = await self.browser.new_context()
        self.page = await context.new_page()
        await self.page.goto(self.url)

    async def solve_captcha(self):
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

    async def input_case_id(self, case_id):
        await self.page.goto(self.url)
        await self.page.click("a:has-text('Case Number')")
        case_number_element = await self.page.query_selector('#CaseNumber')
        await case_number_element.fill(f"{case_id}")
        await self.solve_captcha()

    async def get_court_id(self):
        court_code = "FL_Broward"
        county_name = "Broward"
        county_code = "Broward"

        if court_code not in self.courts:
            self.courts[court_code] = {
                "code": court_code,
                "county_code": county_code,
                "enabled": True,
                "name": f"Florida, {county_name}",
                "state": "FL",
                "type": "TI",
                "source": "FL_Broward county",
                "county": "browawrd"
            }
            self.insert_court(self.courts[court_code])

        return court_code

    async def get_charges_description(self):
        element = await self.page.query_selector("#tblCharges tbody tr td:nth-child(4) b")  
        charges_description = await element.inner_text()
        return charges_description  
    
    async def get_charges(self):
        return await self.page.evaluate('''() => {
            let results = [];
            let table = document.querySelector('#tblCharges');
            if (table) {
                let rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    let result = {};
                    let cell = row.querySelector('td:nth-child(4)');
                    if (cell) {
                        let textContent = cell.innerText.split('\\n');
                        textContent.forEach(line => {
                            let parts = line.split(': ');
                            if (parts.length == 2) {
                                let key = parts[0].trim();
                                let value = parts[1].trim();
                                result[key] = value;
                            }
                        });
                        let vehicleInfoIndex = textContent.findIndex(line => line.includes("Vehicle Information"));
                        if (vehicleInfoIndex !== -1) {
                            for (let i = vehicleInfoIndex + 1; i < textContent.length; i++) {
                                let parts = textContent[i].split(': ');
                                if (parts.length == 2) {
                                    let key = parts[0].trim();
                                    let value = parts[1].trim();
                                    result[key] = value;
                                }
                            }
                        }
                    }
                    results.push(result);
                });
            }
            return results;
        }''')

    async def get_address(self):
        return await self.page.evaluate('''() => {
            const defendantCell = Array.from(document.querySelectorAll('td')).find(td => td.textContent.trim() === 'Defendant');
            if (defendantCell) {
                const row = defendantCell.closest('tr');
                const addressCell = row.querySelectorAll('td')[2];
                if (addressCell) {
                    const addressLines = addressCell.innerHTML.split('<br>');
                    if (addressLines.length >= 2) {
                        const addressPart1 = addressLines[0].trim();
                        const addressPart2 = addressLines.slice(1).join(' ').trim();
                        return `${addressPart1}, ${addressPart2}`;
                    }
                    return addressCell.textContent.trim();
                }
            }
            return null;
        }''')

    async def get_offense_date(self):
        return await self.page.evaluate('''() => {
            const rows = Array.from(document.querySelectorAll('tr'));
            for (let row of rows) {
                if (row.innerText.includes('Date Filed:')) {
                    const cells = Array.from(row.querySelectorAll('td'));
                    for (let cell of cells) {
                        if (cell.getAttribute('width') === '100px') {
                            return cell.textContent.trim();
                        }
                    }
                }
            }
            return null;
        }''')

    async def detail_search(self, case_id):
        await self.page.wait_for_selector(f'a:has-text("{case_id}")')
        await self.page.click(f'a:has-text("{case_id}")')
        await self.page.wait_for_load_state('load')
        
        try:
            filing_date_element = await self.page.query_selector('span:has-text("Filing Date:") + span')
            filing_date = datetime.strptime(await filing_date_element.inner_text(), "%m/%d/%Y")
        except Exception:
            filing_date = None

        try:
            name_element = await self.page.query_selector('td b')
            name = await name_element.inner_text()
            first_name, middle_name, last_name = self.split_full_name(name.strip())
        except Exception:
            first_name, middle_name, last_name = "", "", ""
        
        try:
            gender_element = await self.page.query_selector('td >> text="Gender:"')
            gender = await gender_element.evaluate('(element) => element.nextSibling.nodeValue.trim()')
        except Exception:
            gender = ""

        try:
            dob_element = await self.page.query_selector('td >> text="DOB:"')
            dob = await dob_element.evaluate('(element) => element.nextSibling.nodeValue.trim()')
            date_components = dob.split("/")
            birth_date, year_of_birth = dob, date_components[2]
        except Exception:
            birth_date, year_of_birth = "", ""
        
        try:
            gender_element = await self.page.query_selector('td >> text="Gender:"')
            sex = await gender_element.evaluate('(element) => element.nextSibling.nodeValue.trim()')
        except Exception:
            gender = ""

        try:
            race_element = await self.page.query_selector('td >> text="Race:"')
            race = await race_element.evaluate('(element) => element.nextSibling.nodeValue.trim()')
        except Exception:
            race = ""

        try:
            address = await self.get_address()
            address_line_1, address_city, address_state_code, address_zip = self.parse_full_address(address)
        except Exception:
            address_line_1, address_city, address_state_code, address_zip = "", "", "", ""

        try:
            offense_date = datetime.strptime(await self.get_offense_date(), "%m/%d/%Y")
        except Exception:
            offense_date = None

        try:
            court_code = await self.get_court_id()
        except Exception:
            court_code = ""

        try:
            charges = await self.get_charges()
        except:
            charges = []

        try: 
            charges_description = await self.get_charges_description()
        except:
            charges_description = ""

        case_dict = {
                "case_id": case_id,
                "court_id": court_code,
                "court_code": court_code,
                "address_line_1": address_line_1,
                "address_city": address_city,
                "address_state_code": address_state_code,
                "address_zip": address_zip,
                "filing_date": filing_date,
                "case_date": filing_date,
                "offense_date": offense_date,
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
                "gender": gender,
                "birth_date": birth_date,
                "year_of_birth": year_of_birth,
                "charges": charges,
                "charges_description": charges_description,
                "race": race,
                "sex": sex,
                "state": "FL",
                "status": "new"
            }
        return case_dict

    async def scrape(self):
        last_case_id_nb = self.state.get("last_case_id_nb", 1500)
        last_case_id_nb = int(last_case_id_nb)
        case_id_nb = last_case_id_nb
        not_found_count = 0
        current_year = datetime.now().year

        await self.init_browser()  

        while True:
            try:
                if not_found_count > 10:
                    console.log("Too many filing dates not found. Ending the search.")
                    break

                case_id_nb = last_case_id_nb
                case_id_full = f"{str(current_year)[2:]}{str(case_id_nb).zfill(6)}TI10A"
                last_case_id_nb += 1

                console.log(f"Current searching case_id-{case_id_full}")

                if self.check_if_exists(case_id_full):
                    console.log(f"Case {case_id_full} already exists. Skipping ...")
                    continue

                await self.input_case_id(case_id_full)

                case_details = await self.detail_search(case_id_full)
                if not case_details:
                    console.log(f"Case {case_id_full} not found. Skipping ...")
                    not_found_count += 1
                    continue
                console.log("case_details", case_details)
                not_found_count = 0
                console.log(f"Inserting case {case_id_full}...")
                self.insert_case(case_details)        
                console.log(
                    f"Inserted case {case_id_full}"
                )
                self.insert_lead(case_details)
                console.log(
                    f"Inserted lead {case_id_full}"
                )
                self.state["last_case_id_nb"] = last_case_id_nb
                self.update_state()
            except Exception as e:
                console.log(f"Failed to scaraping - {e}")
                continue

if __name__ == "__main__":
    browardscraper = BrowardScraper()
    asyncio.run(browardscraper.scrape())
    console.log("Done running", __file__, ".")