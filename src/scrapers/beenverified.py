import json
import logging

# Update python path to include the parent directory
import os
from urllib import parse

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


class BeenVerifiedScrapper:
    LOGIN_PAGE_URL = "https://www.beenverified.com/app/login"
    HOME_PAGE_URL = "https://www.beenverified.com/rf/dashboard"
    REPORT_PAGE_URL = "https://www.beenverified.com/api/v5/reports"
    SEARCH_PAGE_URL = "https://www.beenverified.com/rf/search/person"

    def __init__(self, storage_state) -> None:
        self.storage_state = storage_state
        if not os.path.exists(storage_state):
            raise FileNotFoundError(
                f"Storage state file not found: {storage_state}"
            )
        self.consecutive_timeouts = 0
        self.page = None

    async def init_browser(self):
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            storage_state=self.storage_state
        )
        page = await self.context.new_page()
        await page.goto(self.HOME_PAGE_URL)
        return page

    def build_search_url(
        self,
        first_name,
        last_name,
        middle_name: str | None,
        city: str | None = None,
        state: str | None = None,
        age: int | None = None,
    ):
        params = {}
        if city:
            params["city"] = city
        if state:
            params["state"] = state
        if age:
            params["age"] = age
        if first_name:
            params["fname"] = first_name
        if last_name:
            params["ln"] = last_name
        if middle_name:
            params["mn"] = middle_name

        url = parse.urlencode(params)
        url = f"{self.SEARCH_PAGE_URL}?{url}"

        return url

    def score_of_leads(self, result, search_query):
        score = 0

        if (
            search_query.get("first_name").lower() not in result.lower()
            or search_query.get("last_name").lower() not in result.lower()
            or "deceased" in result.lower()
        ):
            score = -1
            return score

        score += result.lower().count("alias")
        score += result.lower().count("relatives")
        score += result.lower().count(
            search_query.get("city").lower()
            if search_query.get("city")
            else ""
        )
        score += result.lower().count(
            search_query.get("state").lower()
            if search_query.get("state")
            else ""
        )
        score += result.lower().count(
            search_query.get("age").lower() if search_query.get("age") else ""
        )
        score += result.lower().count(
            search_query.get("middle_name").lower()
            if search_query.get("middle_name")
            else ""
        )

        return score

    async def open_report_page(self, page, container_user):
        async with page.expect_popup() as popup_info:
            view_report = await container_user.query_selector(
                ".MuiButtonBase-root"
            )
            await view_report.click()
            new_page = await popup_info.value
            return new_page

    async def extract_phone_numbers(self, page):
        container_phone = await page.query_selector("#phone-numbers-section")
        phone_numbers = await container_phone.query_selector_all(
            ".css-1vugsqn"
        )
        phone_numbers = [
            await phone_number.text_content() for phone_number in phone_numbers
        ]
        # Limit to the first 4 numbers
        if len(phone_numbers) > 4:
            phone_numbers = phone_numbers[:4]

        return phone_numbers

    async def extract_addresses(self, page):
        addresses_list = []
        container_address = await page.query_selector(
            "#address-history-section"
        )
        addresses = await container_address.query_selector_all(".css-1q4wjho")
        for address in addresses:
            address_fields = await address.query_selector_all(".css-zv7ju9")
            addresses_txt = [
                await address_field.text_content()
                for address_field in address_fields
            ]
            addresses_list.append(" ".join(addresses_txt))

        return addresses_list

    async def extract_email_list(self, page):

        email_container = await page.query_selector("#email-section")
        email_elements = await email_container.query_selector_all(
            ".css-1vugsqn"
        )
        email_list = [
            await email_element.text_content()
            for email_element in email_elements
        ]
        return email_list

    async def get_lead_info(self, new_page):
        extra_phone_numbers = await self.extract_phone_numbers(new_page)
        extra_addresses = await self.extract_addresses(new_page)
        extra_emails = await self.extract_email_list(new_page)
        return extra_phone_numbers, extra_addresses, extra_emails

    # current from (314) 691-4319 to +13146914319
    def format_phone_number(self, phone_number):
        output = (
            phone_number.replace("(", "")
            .replace(")", "")
            .replace(" ", "")
            .replace("-", "")
        )

        if len(output) == 10:
            return f"+1{output}"
        else:
            return output

    consecutive_timeouts = 0

    async def search_person(
        self,
        first_name,
        last_name,
        middle_name,
        age,
        city="",
        state="",
        zip="",
        dob="",
        address_line1="",
        address_line2="",
    ):
        try:

            search_query = {
                "first_name": str(first_name),
                "last_name": str(last_name),
                "middle_name": str(middle_name),
                "age": str(age),
                "city": str(city),
                "state": str(state),
                "zip": str(zip),
                "addressLine1": str(addressLine1),
                "addressLine2": str(addressLine2),
            }
            # Triggering the search
            url = self.build_search_url(
                first_name, last_name, middle_name, city, state, age
            )
            url_search = url

            if self.page is None or True:
                self.page = await self.init_browser()
            elif len(self.context.pages) > 0:
                self.page = self.context.pages[0]
                for p in self.context.pages[1:]:
                    await p.close()

            await self.page.goto(url)

            # Getting results
            try:
                await self.page.wait_for_selector(".css-ts1zsd")
            except Exception:
                print("Timeout")
                self.consecutive_timeouts += 1
                if self.consecutive_timeouts > 20:
                    print("Too many timeouts")
                    return
                print("No leads found")
                return
            container_results = await self.page.query_selector(".css-ts1zsd")

            if container_results is None:
                print("No leads found")
                return

            try:
                await container_results.wait_for_selector(".css-1mvdt3q")
            except Exception:
                print("Timeout")
                self.consecutive_timeouts += 1
                if self.consecutive_timeouts > 10:
                    print("Too many timeouts")
                    return
                print("No leads found")
                return

            container_users = await container_results.query_selector_all(
                ".css-1mvdt3q"
            )

            self.consecutive_timeouts = 0

            # Measure the score for each lead
            max_score = -1
            max_score_id = -1
            for i, lead in enumerate(container_users):
                results = await lead.text_content()
                score = self.score_of_leads(results, search_query)
                print(f"Score of lead {i} is {score}")
                if score > max_score:
                    max_score = score
                    max_score_id = i

            logger.info(f"Max score is {max_score} for lead {max_score_id}")

            if max_score < 0:
                logger.info("No leads found")
                return

            # Extracting the leads
            selected_lead = container_users[max_score_id]

            # Opening the report page
            new_page = await self.open_report_page(self.page, selected_lead)
            await new_page.wait_for_selector("#person-overview", timeout=60000)

            # Extract the URL link and the parameter ?bvid=N_MTUwMDg3ODcxMjc5
            url = new_page.url
            url_parsed = parse.urlparse(url)
            query = parse.parse_qs(url_parsed.query)
            bvid = query.get("bvid")[0]

            # Post request to get the id of the report
            url = "https://www.beenverified.com/api/v5/reports"

            payload = json.dumps(
                {
                    "report_type": "detailed_person_report",
                    "meta": {"person_id": bvid, "report_flags": []},
                    "h-captcha-response": "",
                }
            )

            # Run the post request with APIRequest
            response = await self.page.evaluate(
                f"""fetch('{url}', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({payload})
                }}).then(res => res.json())"""
            )

            # Extract the permalink
            permalink = response["report"]["permalink"]

            # Call the API to get the report
            api_url = (
                f"https://www.beenverified.com/api/v5/reports/{permalink}"
            )

            # Run the get request with APIRequest
            report = await self.page.evaluate(
                f"""fetch('{api_url}').then(res => res.json())"""
            )

            people = report.get("entities").get("people")

            details = {}
            if people:
                contact_details = people[0].get("contact", {})

                mapping = {
                    "addresses": "address",
                    "emails": "email",
                    "phones": "phone",
                }
                for e in ("addresses", "emails", "phones"):
                    value = contact_details.get(e)
                    if value:
                        # Transform the value list to a dict
                        value = {i: v for i, v in enumerate(value)}
                        details[mapping[e]] = value

            # Extracting the extra info
            # extra_phone_numbers, extra_addresses, extra_emails = (
            #     await self.get_lead_info(new_page)
            # )

            phones = [
                p.get("number")
                for p in details.get("phone", {}).values()
                if p.get("meta").get("confidence") > 65
                and p.get("type") != "home_phone"
            ]

            addresses = [
                a.get("full")
                for a in details.get("address", {}).values()
                if a.get("meta").get("confidence") > 65
            ]

            emails = [
                e.get("address")
                for e in details.get("email", {}).values()
                if e.get("meta").get("confidence") > 65
            ]

            results = {
                "phone_numbers": phones,
                "addresses": addresses,
                "emails": emails,
            }

            details = {
                "phones": [
                    self.format_phone_number(p)
                    for p in results["phone_numbers"]
                ],
                "phone": {
                    str(k): {
                        "phone": self.format_phone_number(p),
                    }
                    for k, p in enumerate(results["phone_numbers"])
                },
                "emails": results["emails"],
                "report": {
                    "addresses": results["addresses"],
                },
                "lead_source": "beenverified",
            }

            details["report"] = report
            for p in self.context.pages[1:]:
                await p.close()
        except Exception as e:
            logger.error(f"Error in beenverified: {e}")
        finally:
            await self.browser.close()

        return details
