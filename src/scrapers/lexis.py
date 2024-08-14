import datetime
import json
import logging
import os
import re

from rich.console import Console

from playwright.async_api import async_playwright
from src.services.emails import GmailConnector
from src.services.leads import (
    LeadsService,
)
from src.services.settings import ScrapersService

console = Console()


logger = logging.getLogger(__name__)

leads_service = LeadsService()


HOME_PAGE_URL = "https://riskmanagement.lexisnexis.com/app/bps/misc#"


class LexisNexisPhoneFinder:
    def __init__(
        self,
        storage_state=None,
        username=None,
        password=None,
        email="ttdwoman@gmail.com",
        proxy=None,
        # proxy="socks5://localhost:9090",
    ) -> None:
        self.storage_state = storage_state
        self.username = username
        self.password = password
        self.email = email
        self.proxy = proxy
        self.browser = None

    async def start_browser(self, new_context=False):
        if self.browser is not None:
            await self.browser.close()

        pw = await async_playwright().start()

        if self.proxy is not None:
            logger.info("Using proxy")
            self.browser = await pw.chromium.launch(
                headless=True, args=["--proxy-server=socks5://localhost:9090"]
            )
        else:
            logger.info("Not using proxy")
            self.browser = await pw.chromium.launch(headless=True)

        if new_context:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
            self.context = await self.browser.new_context(
                user_agent=user_agent
            )
        else:
            self.context = await self.browser.new_context(
                storage_state=self.storage_state
            )

    async def login_form(self, page):

        # Fill the form with the username and password
        await page.fill('input[name="LOGINID"]', self.username)
        await page.fill('input[name="PASSWORD"]', self.password)

        # Click on the submit button
        section = page.locator("#SIGNON")
        element = section.get_by_text("Sign In")
        await element.click()

        # Click on submit otp button
        await page.wait_for_timeout(5000)
        section = page.locator("#send-mfa-token-modal")
        element = page.get_by_role("button", name="Send")

        # If element is visibile click on it
        output = await element.is_visible()

        if output:
            await element.click()

            # Wait for the page to load
            await page.wait_for_timeout(5000)

            # Get the OTP email
            gmail_connector = GmailConnector(user_id=self.email)

            # Get the last email
            emails = gmail_connector.get_inbox_emails(total_results=30)

            for email in emails:
                if "temporary one-time passcode" in email["snippet"]:
                    break

            # Get the OTP code
            otp_code = re.findall(r"\d{6}", email["snippet"])[0]

            # Fill the form with the OTP code
            await page.fill('input[name="OTP1"]', otp_code)

            # Click on the submit button
            section = page.locator("#verify-mfa-token-modal")
            element = section.get_by_role("button", name="Send")
            await element.click()

            # Wait for the page to load
            await page.wait_for_timeout(5000)

            # Click on the continue button
            section = page.locator("#final-mfa-token-modal")
            element = section.get_by_role("button", name="Continue")
            await element.click()

        # Click on the confirm button
        element = page.locator("#permissible_display").get_by_role(
            "button", name="Confirm to Proceed"
        )
        await element.click()

        # Save the session
        await page.wait_for_load_state()
        state = await self.browser.contexts[0].storage_state()
        os.makedirs("playwright/.auth", exist_ok=True)

        if self.storage_state is not None:
            console.log("Saving the session")
            with open(self.storage_state, "w") as file:
                json.dump(state, file)

    async def login(self):

        if self.storage_state is not None and not os.path.exists(
            self.storage_state
        ):
            await self.start_browser(new_context=True)
        else:
            await self.start_browser(new_context=False)

        if self.context.pages is not None and len(self.context.pages) > 0:
            for p in self.context.pages:
                await p.close()

            page = await self.context.new_page()

            raise Exception("Not implemented")

        else:
            page = await self.context.new_page()

        await page.goto(HOME_PAGE_URL)

        # Check if not logged in (form with input[name=email])
        element = await page.get_by_text("Sign In").all()

        if element is not None and element:
            await self.login_form(page)
        else:
            console.log("Already logged in")

        return page

    async def start(self):
        page = await self.login()
        # Click on the a link with the attr data-event="SEARCH2/SHOW_PHONE_FINDER"
        element = page.get_by_role("link").and_(
            page.get_by_text("Phone Finder")
        )
        await element.click()
        return page

    async def close_tabs(self, page):
        # Close all the opened tabs button with class remove-tab except the last one
        elements = await page.get_by_role("button").all()

        async def get_aria_label(elem):
            label = await elem.get_attribute("aria-label")
            if label is None:
                label = ""
            return label.lower()

        tabs_to_close = [
            elem
            for elem in elements
            if "close tab" in await get_aria_label(elem)
        ]
        if len(tabs_to_close) > 1:
            for elem in tabs_to_close[:-1]:
                try:
                    console.log("Closing tab")
                    await elem.click()
                    await page.wait_for_timeout(1000)
                except:
                    pass

    async def search_person(
        self,
        first_name,
        last_name,
        middle_name="",
        dob="",
        age=None,
        city="",
        state="",
        zip="",
        address_line1="",
        address_line2="",
    ):
        if zip is not None:
            zip = str(zip).replace(".0", "")

        # Remove the numbers from the city
        city = re.sub(r"\d+", "", city)

        # Re,ove th
        zip = re.sub(r"\D", "", zip)
        page = await self.start()
        # Wait 5 seconds
        await page.wait_for_timeout(5000)

        # Close all the opened tabs button with class remove-tab except the last one
        await self.close_tabs(page)

        # Fill the form LAST_NAME, FIRST_NAME, MI, STREET_ADDRESS, CITY, STATE, ZIP
        await page.fill("input[name=LAST_NAME]", last_name)
        await page.fill("input[name=FIRST_NAME]", first_name)
        await page.fill("input[name=MI]", middle_name)
        await page.fill("input[name=STREET_ADDRESS]", address_line1)
        await page.fill("input[name=CITY]", city)
        # State is a dropdown
        await page.select_option("select[name=STATE]", state)
        await page.fill("input[name=ZIP]", zip)

        # Select radio PHONE_FINDER_TYPE_B
        element = await page.get_by_role("radio").all()
        for elem in element:
            value = await elem.get_attribute("id")
            if value == "PHONE_FINDER_TYPE_B":
                await elem.click()

        # Click on the search button
        # Find in the element with id = portal-search-buttons
        section = page.locator("#portal-search-buttons")
        # Find the button with the text "Search"
        element = section.get_by_text("Search")
        await element.click()

        # Await until this elements is visible search-results-row

        # Await 30 seconds
        await page.wait_for_timeout(5000)

        # Multiple results found
        text = await page.get_by_text("Multiple identities were found").all()

        if len(text) > 0:
            console.log("Multiple identities were found - Not implemented")
            await self.close()
            return None

        # Find the button download <button type="button" data-placement="bottom" class="btn btn-secondary btn-sm download-icon svg-icon-tiny print-download-dialog" aria-label="Download Results" data-original-title="Download Results" data-download-active-tab="767ae742d9f0307032ce888306d2555c" data-tab_id="767ae742d9f0307032ce888306d2555c" data-type="download"></button>
        text = await page.get_by_text(
            "No documents were found for your search terms."
        ).all()

        if len(text) > 0:
            await page.close()
            console.log("No documents were found for your search terms.")
            await self.close()
            return None

        # Click on the download button
        element = await page.locator("button[data-type=download]").all()
        for elem in element:
            await elem.click()
            break

        # Wqit 5 seconds
        await page.wait_for_timeout(5000)
        # Select from the dropdown with id DOWNLOAD_FORMAT the option download_format_html
        element = page.locator("select#DOWNLOAD_FORMAT").first
        await element.select_option("HTML")

        async with page.expect_download() as download_info:
            element = page.locator("button.start-verify-print-download").first
            await element.click()

        download = await download_info.value
        await download.save_as("temp/" + download.suggested_filename)

        # Read the file with filereader
        with open("temp/" + download.suggested_filename, "r") as file:
            data = file.read()

        # Close the page

        # Extract with re phone numbers with the format 123-456-7890

        phones = re.findall(r"\d{3}-\d{3}-\d{4}", data)

        # Generated the report
        scraper_service = ScrapersService()
        scraper = scraper_service.get_single_item("lexis_nexis_phone_finder")

        if scraper is None:
            current_date = datetime.datetime.now().date()
            scraper = scraper_service.set_item(
                "lexis_nexis_phone_finder",
                {"count": {str(current_date): 1}},
            )

        else:
            current_date = datetime.datetime.now().date()
            count = scraper.count
            if count is None:
                count = {}
            count[str(current_date)] = count.get(str(current_date), 0) + 1
            scraper_service.patch_item(
                "lexis_nexis_phone_finder",
                {"count": count},
            )

        phones = [f"+1{p.replace('-', '')}" for p in set(phones)]

        details = {
            "phones": phones,
            "phone": {
                str(k): {
                    "phone": p,
                }
                for k, p in enumerate(phones)
            },
            "email": None,
            "report": {"data": data},
            "lead_source": "lexis_nexis_phone_finder",
        }

        await self.close()

        return details

    async def close_pages(self):
        for page in self.context.pages:
            await page.close()

    async def close(self):
        if self.browser is not None:
            await self.browser.close()
            self.browser = None
