import json
import logging
import os
import urllib.parse
from datetime import datetime
from time import sleep
from urllib.parse import parse_qs, urlparse

import selenium.common.exceptions
from rich.console import Console
from selenium import webdriver

#  from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from twilio.rest import Client

from src.core import tools
from src.core.config import get_settings

settings = get_settings()

logger = logging.Logger(__name__)
console = Console()


class CaptchaException(Exception):
    pass


class BeenVerifiedScrapper:
    def __init__(self, cache=False):
        self.options = Options()
        self.options.add_argument("--no-sandbox")

        # self.options.add_argument("--headless")
        self.options.add_argument("enable-automation")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--window-size=1920,1080")

        # Selenium with
        self.vars = {}
        self.cache = cache
        self.magic_link = None
        self.email_sensor = None
        if not cache:
            self.driver = webdriver.Firefox(options=self.options)
            # self.driver = webdriver.Chrome(options=self.options)
            # self.driver = webdriver.Remote(
            #     command_executor=settings.SELENIUM_STANDALONE_URL,
            #     options=self.options,
            # )
            self.login()

    def __hash__(self):
        return 1

    def teardown(self):
        if self.driver is not None:
            self.driver.quit()

    def login(self):
        self.driver.get("https://www.beenverified.com/app/login")
        # 2 | setWindowSize | 1680x1005 |
        # self.driver.set_window_size(1680, 1005)
        # 3 | click | css=.nav__utils-btn:nth-child(2) > .nav__utils-link |
        try:
            # 4 | type | click on the magic link
            self.driver.find_element(By.ID, "magic_link").click()

            sleep(5)

            # 5 | type | id=magic-link-email-field |
            self.driver.find_element(By.ID, "magic-link-email-field").click()

            # 5 | type | id=login-password | Marcus1995!
            self.driver.find_element(By.ID, "magic-link-email-field").send_keys(
                os.environ.get("BEEN_VERIFIED_EMAIL", "fublooman@gmail.com")
            )
            # 6 | click on connect
            self.driver.find_element(
                By.CSS_SELECTOR, "#send-magic-link-form > .btn"
            ).click()
            console.log("Waiting 60 seconds")
            sleep(5)

            # get the magic link
            sns = tools.SensorEmail()
            console.log("Waiting for the magic link")
            magic_link = sns()

            # 7 | open | magic link
            self.magic_link = magic_link
            self.email_sensor = sns
            self.driver.get(magic_link)
            sleep(60)
        except Exception as e:
            self.driver.save_screenshot(
                f"beenverified-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.png"
            )
            logger.warning(
                "Continuing with the session as probably the user is already logged in"
            )

            logger.debug(f"Issue with Beenverified {e}")

    def get_score(self, result, search_query):
        score = 0

        if search_query.get("first_name") not in result.text.lower():
            score = -1
            return score
        if search_query.get("last_name") not in result.text.lower():
            score = -1
            return score
        if "deceased" in result.text.lower():
            score = -1
            return score
        score = 0

        if "alias" in result.text.lower():
            score += 1

        if "relatives" in result.text.lower():
            score += 1

        if search_query.get("city") in result.text.lower():
            score += 1

        if search_query.get("state") in result.text.lower():
            score += 1

        if search_query.get("age") in result.text.lower():
            score += 1

        if search_query.get("middle_name") in result.text.lower():
            score += 1

        return score

    def retrieve_information(self, link):
        if self.cache:
            self.driver = webdriver.Chrome(options=self.options)
            # self.driver = webdriver.Remote(
            #     command_executor=settings.SELENIUM_STANDALONE_URL,
            #     options=self.options,
            # )
            self.login()

        output = {
            "name": "",
            "details": "",
            "phone": "",
            "exact_match": True,
            "error": True,
        }
        # 7 | open the search screen
        self.driver.get(link)
        # 8 | waitForElementPresent | css=.recent-reports__report | 30000
        try:
            WebDriverWait(self.driver, 30).until(
                expected_conditions.presence_of_element_located(
                    (By.CSS_SELECTOR, ".person-search-result-card")
                ),
                "No results found",
            )
        except selenium.common.exceptions.TimeoutException:
            logger.error(f"An issue happened for {link}")
            # Take screenshot
            self.driver.save_screenshot(
                f"beenverified-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.png"
            )
            return None

        # Check the results:
        try:
            results_count = self.driver.find_element(
                By.CSS_SELECTOR, ".results-count"
            ).text
        except selenium.common.exceptions.NoSuchElementException:
            logger.error(f"No results found for {link}")
            results_count = "Error"

        if "no exact match" in results_count.lower():
            output["exact_match"] = False  # TODO: return output
            return output

        # Go through the results:
        try:
            results = self.driver.find_elements(
                By.CSS_SELECTOR, ".person-search-result-card"
            )
        except selenium.common.exceptions.NoSuchElementException:
            logger.error(f"No approximate results found for {link}")
            return output

        # Focus on the first element:
        # Example of the results.text results[0].text
        # 'NAME MATCH\nJoseph Ruvin\nDeceased\nBrooklyn, NY\nBorn\nJul 1892\nKnown locations\nBrooklyn, NY\nView person report'

        # Extract the params from the link
        parsed_url = urlparse(link)
        params = parse_qs(parsed_url.query)

        def get_param(params, key):
            if params.get(key):
                return params.get(key)[0].lower()
            else:
                return ""

        query = {
            "first_name": get_param(params, "fname"),
            "last_name": get_param(params, "ln"),
            "middle_name": get_param(params, "mn"),
            "state": get_param(params, "state"),
            "city": get_param(params, "city"),
            "age": get_param(params, "age"),
        }

        attribute_id = None

        search_score = [self.get_score(result, query) for result in results]

        # Get the index and value of the max score
        max_score = max(search_score)
        index_max_score = search_score.index(max_score)

        if max_score == -1:
            output["exact_match"] = False
            logger.error(f"No relevant results found for {link}")
            return output

        # Get the attribute id of the element with the max score
        attribute_id = results[index_max_score].get_attribute("id")

        # Initial window handle
        window_handles = self.driver.window_handles.copy()

        self.driver.find_element(By.CSS_SELECTOR, f"#{attribute_id} .btn").click()

        # Check if blocked here by the captcha
        try:
            # Find the element that has the captcha warning with class whoops-body-sub-title
            WebDriverWait(self.driver, 5).until(
                expected_conditions.presence_of_element_located(
                    (By.CSS_SELECTOR, ".whoops-body-sub-title")
                )
            )
            logger.error("Blocked by captcha")

            # Send a message to me and Shawn to check
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

            sms_message = (
                f"Connect to solve the captcha for the BeenVerified Scraper {link}"
            )

            phone_ayoub = "+33674952271"
            phone_shawn = "+1816518-8838"

            client.messages.create(
                messaging_service_sid=settings.TWILIO_MESSAGE_SERVICE_SID,
                body=sms_message,
                to=phone_ayoub,
            )
            client.messages.create(
                messaging_service_sid=settings.TWILIO_MESSAGE_SERVICE_SID,
                body=sms_message,
                to=phone_shawn,
            )

            raise CaptchaException("Blocked by captcha")
        except selenium.common.exceptions.TimeoutException:
            pass

        sleep(5)

        # Close the previous tabs
        for w in window_handles:
            self.driver.switch_to.window(w)
            self.driver.close()

        self.driver.switch_to.window(self.driver.window_handles[-1])

        WebDriverWait(self.driver, 60).until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, ".report-header__title")
            )
        )
        # 12 | click | css=.report_section__label_title |

        # Parse the url to get the permalink
        parsed_url = urllib.parse.urlparse(self.driver.current_url)

        # Get the permalink from the params of the url
        permalink = urllib.parse.parse_qs(parsed_url.query)["permalink"][0]

        # Get the report in Json format from the API endpoint
        # e.g https://www.beenverified.com/api/v5/reports/40d4f669eb79ad6d46d79eca80c5699bcee9a34e7f5d4e3edddbc2
        api_url = f"https://www.beenverified.com/api/v5/reports/{permalink}"

        # Get the report using Selenium and parse it to Json
        report = self.driver.execute_script(
            f"return fetch('{api_url}').then(response => response.json());"
        )

        output["report"] = report

        people = report.get("entities").get("people")

        if people:
            contact_details = people[0].get("contact", {})

            if contact_details is None:
                logger.error(f"No contact details found for {link}")
                output["exact_match"] = False
                return output
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
                    output[mapping[e]] = value

        try:
            summary = self.driver.find_element(
                By.CSS_SELECTOR, ".report-header__container__info"
            ).text
            output["details"] = summary
        except selenium.common.exceptions.NoSuchElementException:
            logger.error(f"No details found for {link}")
            return output
        output["error"] = False
        return output

    def get_beenverified_link(
        self,
        first_name=None,
        last_name=None,
        middle_name=None,
        year=None,
        state="MO",
        city=None,
    ):
        # state = "MO"
        url = f"https://www.beenverified.com/app/search/person?"
        if first_name is not None:
            url += f"fname={first_name}&"
        if last_name is not None:
            url += f"ln={last_name}&"
        if middle_name is not None:
            url += f"mn={middle_name}&"
        if state is not None:
            url += f"state={state}&"
        if city is not None:
            url += f"city={city}&"
        if year is not None:
            try:
                age = datetime.now().year - year
                url += f"age={age}"
            except Exception as e:
                year = None
                logger.error(f"Error parsing the year. Exception{e} ")
        return url


if __name__ == "__main__":
    link = (
        "https://www.beenverified.com/app/search/person?fname=ETHAN&ln"
        "=NEARY&mn=NATHANIEL&state=MO&age=18"
    )

    scrapper = BeenVerifiedScrapper()
    try:
        data = scrapper.retrieve_information(link)
    except Exception as e:
        print(e)
    finally:
        scrapper.teardown()
