import logging
import os
from time import sleep

import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from commonregex import CommonRegex

import config
from core import tools, storage

logger = logging.Logger(__name__)


class BeenVerifiedScrapper:
    def __init__(self, cache=False):
        self.options = Options()
        # self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("enable-automation")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--disable-dev-shm-usage")
        chrome_profile_path = os.environ.get(
            "CHROME_PROFILE_PATH",
            '/Users/aennassiri/Library/Application Support/Google/Chrome'
        )
        self.options.add_argument("user-data-dir=" + chrome_profile_path)
        self.options.add_argument("--profile-directory=Profile 1")

        # Selenium with
        self.vars = {}
        self.cache = cache
        self.driver = None
        if not cache:
            self.driver = webdriver.Chrome(options=self.options)
            self.login()

    def __hash__(self):
        return 1

    def teardown(self):
        if self.driver is not None:
            self.driver.quit()

    def login(self):
        self.driver.get("https://www.beenverified.com/")
        # 2 | setWindowSize | 1680x1005 |
        # self.driver.set_window_size(1680, 1005)
        # 3 | click | css=.nav__utils-btn:nth-child(2) > .nav__utils-link |
        try:
            self.driver.find_element(
                By.CSS_SELECTOR,
                ".nav__utils-btn:nth-child(2) > "
                ".nav__utils-link"
            ).click()
            # 4 | type | id=login-email | sam@masfirm.net
            self.driver.find_element(By.ID, "login-email").send_keys(
                os.environ.get("BEEN_VERIFIED_EMAIL",
                               "ayoub.ennassiri@neoinvest.ai")
            )
            # 5 | type | id=login-password | Marcus1995!
            self.driver.find_element(By.ID, "login-password").send_keys(
                os.environ.get("BEEN_VERIFIED_PASSWORD", "Murex2019!")
            )
            # 6 | click on connect
            self.driver.find_element(By.ID, "submit").click()
            sleep(30)
        except Exception:
            logger.warning(
                f"Continuing with the session as probably the user is already logged in")

    @tools.cached(storage=storage.RemotePickleStorage(url=config.remote_upload_url))
    def retrieve_information(self, link):
        if self.cache:
            self.driver = webdriver.Chrome(options=self.options)
            self.login()

        output = {
            "name": "",
            "details": "",
            "phone": "",
            "exact_match": True,
            "error": True
        }
        # 7 | open the search screen
        self.driver.get(link)
        # 8 | waitForElementPresent | css=.recent-reports__report | 30000
        WebDriverWait(self.driver, 30).until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, ".person-search-result-card")))
        # Check the results:
        try:
            results_count = self.driver.find_element(
                By.CSS_SELECTOR, ".results-count"
            ).text
        except selenium.common.exceptions.NoSuchElementException as e:
            logger.error(f"No results found for {link}")
            results_count = "Error"

        if "no exact match" in results_count:
            output["exact_match"] = False

        # Go through the results:
        try:
            results = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".person-search-result-card"
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

        # Close the previous tabs
        sleep(5)
        for w in window_handles:
            self.driver.switch_to.window(w)
            self.driver.close()

        self.driver.switch_to.window(self.driver.window_handles[-1])

        WebDriverWait(self.driver, 30).until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, ".report-header__title")))
        # 12 | click | css=.report_section__label_title |

        try:
            informations = [
                i.text for i in self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".report-overview__section-summary-content")
            ]
            output["address"] = informations[0]
            output["phone"] = informations[1]
            output["email"] = informations[2]

        except selenium.common.exceptions.NoSuchElementException:
            logger.error(f"No informations found for {link}")

            return output

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
