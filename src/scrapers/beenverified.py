import logging
import os
from datetime import datetime
from time import sleep

import selenium.common.exceptions
from rich.console import Console
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from src.core import tools
from src.core.config import get_settings

settings = get_settings()

logger = logging.Logger(__name__)
console = Console()


class BeenVerifiedScrapper:
    def __init__(self, cache=False):
        self.options = Options()
        self.options.add_argument("--no-sandbox")
        # self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("enable-automation")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--disable-dev-shm-usage")
        # self.options.add_argument("--window-size=1920,1080")

        # Selenium with
        self.vars = {}
        self.cache = cache
        self.magic_link = None
        self.email_sensor = None
        if not cache:
            self.driver = webdriver.Chrome(options=self.options)
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
            self.driver.find_element(
                By.ID, "magic-link-email-field"
            ).send_keys(
                os.environ.get("BEEN_VERIFIED_EMAIL", "fublooman@gmail.com")
            )
            # 6 | click on connect
            self.driver.find_element(
                By.CSS_SELECTOR, "#send-magic-link-form > .btn"
            ).click()
            console.log("Waiting 60 seconds")
            sleep(60)

            # get the magic link
            sns = tools.SensorEmail()
            console.log("Waiting for the magic link")
            magic_link = sns()

            # 7 | open | magic link
            self.magic_link = magic_link
            self.email_sensor = sns
            self.driver.get(magic_link)
            sleep(30)
        except Exception as e:
            self.driver.save_screenshot(
                f"beenverified-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.png"
            )
            logger.warning(
                "Continuing with the session as probably the user is already logged in"
            )

            logger.debug(f"Issue with Beenverified {e}")

    def retrieve_information(self, link):
        if self.cache:
            self.driver = webdriver.Chrome(options=self.options)
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
            output["exact_match"] = False

        # Go through the results:
        try:
            results = self.driver.find_elements(
                By.CSS_SELECTOR, ".person-search-result-card"
            )
        except selenium.common.exceptions.NoSuchElementException:
            logger.error(f"No approximate results found for {link}")
            return output

        # Focus on the first element:
        attribute_id = results[0].get_attribute("id")

        # Initial window handle
        window_handles = self.driver.window_handles.copy()

        self.driver.find_element(
            By.CSS_SELECTOR, f"#{attribute_id} .btn"
        ).click()

        # Check if blocked here by the captcha
        try:
            # Find the element that has the captcha warning with class whoops-body-sub-title
            WebDriverWait(self.driver, 5).until(
                expected_conditions.presence_of_element_located(
                    (By.CSS_SELECTOR, ".whoops-body-sub-title")
                )
            )
            logger.error("Blocked by captcha")
        except selenium.common.exceptions.TimeoutException:
            pass

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

        try:
            informations = [
                i.text
                for i in self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".report-overview__section-summary-content",
                )
            ]
            output["address"] = informations[0]
            output["phone"] = informations[1]
            output["email"] = informations[2]

        except selenium.common.exceptions.NoSuchElementException:
            logger.error(f"No informations found for {link}")
            return None

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
    ):
        state = "MO"
        url = f"https://www.beenverified.com/app/search/person?"
        if first_name is not None:
            url += f"fname={first_name}&"
        if last_name is not None:
            url += f"ln={last_name}&"
        if middle_name is not None:
            url += f"mn={middle_name}&"
        if state is not None:
            url += f"state={state}&"
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
