# Import necessary libraries
import asyncio
import os
import os.path
import sys
import re

# Import specific modules from libraries
from playwright.async_api import async_playwright
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress
from twocaptcha import TwoCaptcha
from tempfile import NamedTemporaryFile

from src.scrapers.base.scraper_base import ScraperBase

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    + "/libraries"
)

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
)

load_dotenv()
TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')

console = Console()

class KansasScraper(ScraperBase):
    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        case_id: str | None = None,
    ) -> None:
        self.email = email
        self.password = password
        # TODO change the values
        self.case_id = case_id or "WY-2024-TR-001995"
        super().__init__(email, password)
        console.log(f" we are seaeching for {self.case_id}")

    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)

    def to_datetime(self, date_str):
        if date_str is None:
            return None
        else:
            return datetime.strptime(date_str, '%m/%d/%Y')
        
    def split_full_name(self, name):
        # Use regular expression to split on space, comma, hyphen, or period.
        parts = re.split(r'[\s,\-\.]+', name)
        
        # Prepare variables for first, middle, and last names
        first_name = middle_name = last_name = ''

        if len(parts) > 2:
            first_name = parts[0]
            middle_name = ' '.join(parts[1:-1])  
            last_name = parts[-1]
        elif len(parts) == 2:
            first_name, last_name = parts
        elif len(parts) == 1:
            first_name = parts[0]

        return first_name, middle_name, last_name
    
    async def init_browser(self):
        console.log("Initation of Browser...")
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(headless=False)
        context = await self.browser.new_context()
        self.page = await context.new_page()
        self.url = "https://prodportal.kscourts.org/ProdPortal/"
        await self.page.goto(self.url)

        sigin_in_button = await self.page.query_selector("#dropdownMenu1")
        if sigin_in_button:
            await sigin_in_button.click()
        else:
            print("The submit button was not found")
        
        all_a_tags = await self.page.query_selector_all('a')

        sign_in_element = None
        for a_tag in all_a_tags:
            text = await a_tag.inner_text()
            if "Sign In" in text:
                sign_in_element = a_tag
                break
            
        if sign_in_element:
            print("Found sign-in button")
            await sign_in_element.click()
        else:
            print("Not Found sign-in button")
       
        await self.page.wait_for_load_state('networkidle')

    async def singin(self, user_name, password):
        user_name_element = await self.page.wait_for_selector('#UserName')
        if user_name_element:
            await self.page.fill('#UserName', user_name)
        
        password_element = await self.page.wait_for_selector('#Password')
        if password_element:
            await self.page.fill('#Password', password)
        
        checkbox_element = await self.page.wait_for_selector('#TOSCheckBox')

        if checkbox_element:
            await self.page.check('#TOSCheckBox')
            print("Checkbox checked successfully!")
        else:
            print("Checkbox not found!")

        submit_button = await self.page.query_selector("#btnSignIn")
        if submit_button:
            await submit_button.click()
        else:
            print("The submit button was not found")
        
        await self.page.wait_for_load_state('networkidle')
    
    async def case_name_search(self, case_id):
        a_tag_selector = 'a.btn.btn-lg.btn-default.portlet-buttons'

        # Wait for the element to be available
        a_tag_element = await self.page.wait_for_selector(a_tag_selector)

        if a_tag_element:
            # Click the <a> tag
            await a_tag_element.click()
            print("Clicked the <a> tag successfully!")
            await self.page.wait_for_load_state('networkidle')
        else:
            print("The <a> tag with the specified class was not found!")
        
        case_number_input_element = await self.page.wait_for_selector("#caseCriteria_SearchCriteria")
        if case_number_input_element:
            await case_number_input_element.fill(case_id)
    
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
        
        submit_button = await self.page.query_selector("#btnSSSubmit")
        if submit_button:
            await submit_button.click()
        else:
            print("The submit button was not found")

        await self.page.wait_for_load_state('networkidle')

        # Wait for the <a> tag containing the specific text to be available
        await self.page.wait_for_selector(f'a.caseLink:has-text("{case_id}")')
        element = await self.page.query_selector(f'a.caseLink:has-text("{case_id}")')

        name_locator = self.page.locator('td.card-data.party-case-partyname[data-label="Party Name"]')
        try:
            # Try to extract the inner text
            name = await name_locator.inner_text()
            name = name.strip()  # Ensure no leading/trailing whitespace
        except:
            # Handle any exceptions by setting name to None
            name = ""

        first_name, middle_name, last_name = self.split_full_name(name)
        case_dict = {
                        "case_id": case_id,
                        "first_name": first_name,
                        "middle_name": middle_name,
                        "last_name": last_name,
                    }
        # Get the 'data-url' attribute value
        data_url = await element.get_attribute("data-url") if element else None
        self.url = f"https://prodportal.kscourts.org/{data_url}"
        await self.page.goto(self.url)
        await self.page.wait_for_load_state('networkidle')
        return case_dict
    
    async def find_date_by_label(self, label_text):
        await self.page.wait_for_selector(f'div.roa-label.ng-binding.flex:has-text("{label_text}")')
        label_div = await self.page.query_selector(f'div.roa-label.ng-binding.flex:has-text("{label_text}")')
        if label_div:
            print("Found that element")
            date_div = await self.page.evaluate_handle('(label) => label.nextElementSibling', label_div)
            span_element = await date_div.query_selector('span.ng-binding.ng-scope')
            if span_element:
                date_text = await span_element.text_content()
                return date_text.strip()
        return None
    
    async def get_charges(self):
        rows = await self.page.query_selector_all('tr.hide-sm.hide-xs.ng-scope')
        charges = []
        for row in rows:
            charge_dict = {}                
            offense_description = await row.query_selector('td:nth-child(2) .ng-binding')
            citation_number = await row.query_selector('td:nth-child(3) div.ng-binding:nth-child(2)')
            statute = await row.query_selector('td:nth-child(4) div.ng-binding:nth-child(2)')
            degree = await row.query_selector('td:nth-child(5) div.ng-binding:nth-child(2)')
            offense_date = await row.query_selector('td:nth-child(6) div.ng-binding:nth-child(2)')
            filed_date = await row.query_selector('td:nth-child(7) div.ng-binding:nth-child(2)')
            
            # Extract text content and strip any extraneous whitespace
            if offense_description:
                charge_dict['offense_description'] = (await offense_description.text_content()).strip()
            if citation_number:
                charge_dict['citation_number'] = (await citation_number.text_content()).strip()
            if statute:
                charge_dict['statute'] = (await statute.text_content()).strip()
            if degree:
                charge_dict['degree'] = (await degree.text_content()).strip()
            if offense_date:
                charge_dict['offense_date'] = (await offense_date.text_content()).strip()
            if filed_date:
                charge_dict['filed_date'] = (await filed_date.text_content()).strip()

            # Append the current charge dictionary to the charges list
            charges.append(charge_dict)

        for charge in charges:
                print(charge)
            
        return charges
    
    async def get_location(self):
        label_text = "Location"
        location = await self.find_date_by_label(label_text)
        kansas_counties = {
            "Allen County": "Iola",
            "Anderson County": "Garnett",
            "Atchison County": "Atchison",
            "Barber County": "Medicine Lodge",
            "Barton County": "Great Bend",
            "Bourbon County": "Fort Scott",
            "Brown County": "Hiawatha",
            "Butler County": "El Dorado",
            "Chase County": "Cottonwood Falls",
            "Chautauqua County": "Sedan",
            "Cherokee County": "Baxter Springs",
            "Cheyenne County": "St. Francis",
            "Clark County": "Ashland",
            "Clay County": "Clay Center",
            "Cloud County": "Concordia",
            "Coffey County": "Burlington",
            "Comanche County": "Coldwater",
            "Cowley County": "Arkansas City",
            "Crawford County": "Pittsburg",
            "Decatur County": "Oberlin",
            "Dickinson County": "Abilene",
            "Doniphan County": "Troy",
            "Douglas County": "Lawrence",
            "Edwards County": "Kinsley",
            "Elk County": "Howard",
            "Ellis County": "Hays",
            "Ellsworth County": "Ellsworth",
            "Finney County": "Garden City",
            "Ford County": "Dodge City",
            "Franklin County": "Ottawa",
            "Geary County": "Junction City",
            "Gove County": "Quinter",
            "Graham County": "Hill City",
            "Grant County": "Ulysses",
            "Gray County": "Cimarron",
            "Greeley County": "Tribune",
            "Greenwood County": "Eureka",
            "Hamilton County": "Syracuse",
            "Harper County": "Anthony",
            "Harvey County": "Newton",
            "Haskell County": "Sublette",
            "Hodgeman County": "Jetmore",
            "Jackson County": "Holton",
            "Jefferson County": "Valley Falls",
            "Jewell County": "Mankato",
            "Johnson County": "Overland Park",
            "Kearny County": "Lakin",
            "Kingman County": "Kingman",
            "Kiowa County": "Greensburg",
            "Labette County": "Parsons",
            "Lane County": "Dighton",
            "Leavenworth County": "Leavenworth",
            "Lincoln County": "Lincoln",
            "Linn County": "Pleasanton",
            "Logan County": "Oakley",
            "Lyon County": "Emporia",
            "McPherson County": "McPherson",
            "Marion County": "Hillsboro",
            "Marshall County": "Marysville",
            "Meade County": "Meade",
            "Miami County": "Paola",
            "Mitchell County": "Beloit",
            "Montgomery County": "Coffeyville",
            "Morris County": "Council Grove",
            "Morton County": "Elkhart",
            "Nemaha County": "Seneca",
            "Neosho County": "Chanute",
            "Ness County": "Ness City",
            "Norton County": "Norton",
            "Osage County": "Osage City",
            "Osborne County": "Osborne",
            "Ottawa County": "Minneapolis",
            "Pawnee County": "Larned",
            "Phillips County": "Phillipsburg",
            "Pottawatomie County": "Wamego",
            "Pratt County": "Pratt",
            "Rawlins County": "Atwood",
            "Reno County": "Hutchinson",
            "Republic County": "Belleville",
            "Rice County": "Lyons",
            "Riley County": "Manhattan",
            "Rooks County": "Plainville",
            "Rush County": "La Crosse",
            "Russell County": "Russell",
            "Saline County": "Salina",
            "Scott County": "Scott City",
            "Sedgwick County": "Wichita",
            "Seward County": "Liberal",
            "Shawnee County": "Topeka",
            "Sheridan County": "Hoxie",
            "Sherman County": "Goodland",
            "Smith County": "Smith Center",
            "Stafford County": "St. John",
            "Stanton County": "Johnson City",
            "Stevens County": "Hugoton",
            "Sumner County": "Wellington",
            "Thomas County": "Colby",
            "Trego County": "WaKeeney",
            "Wabaunsee County": "Alma",
            "Wallace County": "Sharon Springs",
            "Washington County": "Washington",
            "Wichita County": "Leoti",
            "Wilson County": "Neodesha",
            "Woodson County": "Yates Center",
            "Wyandotte County": "Kansas City"
        }
        location = kansas_counties[location]
        return location
    
    async def get_court_id(self):
        # Locate the specific td element where the citation number is located
        court_ids = await self.page.query_selector_all('roa-charge-data-column[label="Citation"]')
        for element in court_ids:
            court_id = await element.get_attribute('data-value')
            if court_id:
                return court_id.strip()
        return None
    
    async def get_case_detail(self, case_id):
        case_dict1 = await self.case_name_search(case_id)


        label_text = "Filed"
        try:
            filing_date = await self.find_date_by_label(label_text)
            filing_date = self.to_datetime(filing_date)
        except:
            filing_date = None
        
        label_text = "Location"
        try:
            location = await self.get_location()
        except:
            location = None

        try:
            charges = await self.get_charges()
        except:
            charges = None

        court_id = await self.get_court_id()
        
        try:
            case_type_element = self.page.locator("text='Case Type:'").first
            case_type = await case_type_element.evaluate('node => node.nextElementSibling.innerText')        
            case_type = case_type.strip()
        except:
            case_type = None

        try:
            case_status_parent = self.page.locator("text='Case Status:'").first
            case_status = await case_status_parent.evaluate("(element) => element.parentElement.querySelector('.roa-value .roa-text-bold .ng-binding:nth-child(3)').innerText")
            case_status = case_status.strip()
        except:
            case_status = None
        
        try:
            date_element = self.page.locator('roa-charge-data-column[ng-if="::charge.OffenseDate"] .ng-binding').nth(1)
            offense_date = await date_element.inner_text()
            offense_date = offense_date.strip()
            offense_date = self.to_datetime(offense_date)
        except:
            date_element = None

        case_dict2 = {
                        "court_id": court_id,
                        "filing_date": filing_date,
                        "offense_date": offense_date,
                        "location": location,
                        "charges": charges,
                        "case_type": case_type,
                        "case_status": case_status,
                    }
        
        case_dict = case_dict1.copy()
        for key, value in case_dict2.items():
            if key in case_dict:
                case_dict[key] += value
            else:
                case_dict[key] = value
        
        return case_dict
    
    async def scrape(self, search_parameters):
        user_name = search_parameters["user_name"]
        password = search_parameters["password"]
        case_id = search_parameters["case_id"]
        
        await self.init_browser()
        await self.singin(user_name, password)

        case_dict = await self.get_case_detail(case_id)
        with NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as f:
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
        
            await self.browser.close()
        
        await self.browser.close()

if __name__ == "__main__":
    load_dotenv()
    search_parameters = {
        "user_name": "Smahmudlaw@gmail.com", 
        "password": "Shawn1993!",
    }
    kansasscraper = KansasScraper()
    asyncio.run(kansasscraper.scrape(search_parameters))
    console.log("Done running", __file__, ".")