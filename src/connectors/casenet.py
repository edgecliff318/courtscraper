import logging
import os
import urllib.parse
from datetime import datetime
from time import sleep

from rich.console import Console
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from src.core.config import get_settings

console = Console()

settings = get_settings()

logger = logging.Logger(__name__)
console = Console()


class CaptchaException(Exception):
    pass


class CaseNetWebConnector:
    def __init__(self, cache=False, params=None):
        self.options = Options()
        self.options.add_argument("--no-sandbox")
        # self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("enable-automation")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--disable-dev-shm-usage")

        # Use http://localhost:4444

        # self.options.add_argument("--window-size=1920,1080")

        # Selenium with
        self.vars = {}
        self.cache = cache
        self.params = params
        if params is None:
            self.params = {}
        else:
            self.params = params
        self.email_sensor = None
        if not cache:
            self.driver = webdriver.Remote(
                command_executor=settings.SELENIUM_STANDALONE_URL,
                options=self.options,
            )
            console.print("Chrome Driver started")
            self.login()
            console.print("Logged to casenet")

    def __hash__(self):
        return 1

    def teardown(self):
        if self.driver is not None:
            self.driver.quit()

    def login(self):
        self.driver.get("https://www.courts.mo.gov/cnet/logon.do")
        # 2 | setWindowSize | 1680x1005 |
        # self.driver.set_window_size(1680, 1005)
        # 3 | click | css=.nav__utils-btn:nth-child(2) > .nav__utils-link |
        try:
            # 3 | type | name=username | smeyer4040
            self.driver.find_element(By.NAME, "username").send_keys(
                settings.CASE_NET_USERNAME
            )
            # 4 | type | name=password | MASdorm1993!MAS
            self.driver.find_element(By.NAME, "password").send_keys(
                settings.CASE_NET_PASSWORD
            )
            # 5 | click | css=span > strong |
            self.driver.find_element(By.CSS_SELECTOR, "span > strong").click()
            # Confirm login
            WebDriverWait(self.driver, 30).until(
                expected_conditions.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        ".navbar-right > .dropdown:nth-child(2) .caret",
                    )
                )
            )
        except Exception as e:
            self.driver.save_screenshot(
                f"casenet-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.png"
            )
            logger.error(f"An issue happened while logging in to casenet {e}")
            raise e

    def submit_document(self, filepath_document, case_number, court_location):
        if self.cache:
            self.driver = webdriver.Chrome(options=self.options)
            self.login()

        # If filepath is not in absolute
        if not os.path.isabs(filepath_document):
            filepath_document = os.path.abspath(filepath_document)
        # 1 | Go to the page
        court_location_parsed = urllib.parse.quote(court_location)
        self.driver.get(
            f"https://www.courts.mo.gov/ecf/secure/search.do?"
            f"caseNumber={case_number}&courtLocation={court_location_parsed}&foec=y"
        )

        console.print(
            f"Submitting document to {court_location} for case {case_number}"
        )

        # 2 | click | id=continue |
        self.driver.find_element(By.ID, "continue").click()
        # 3 | click | id=continue |
        sleep(1)
        self.driver.find_element(By.ID, "continue").click()
        # 4 | addSelection | id=onBehalfOf | label=KIERVELYNNE LOUISE BRUNIN
        dropdown = self.driver.find_element(By.ID, "onBehalfOf")

        # Loop through the options and select all of them
        options = dropdown.find_elements(by=By.TAG_NAME, value="option")

        for option in options:
            option.click()

        # 5 | click | id=addBehalfOf |
        self.driver.find_element(By.ID, "addBehalfOf").click()
        console.print("Added on behalf of")

        sleep(1)

        # 11 | select | id=filter | label=Filing - Other/Miscellaneous
        dropdown = self.driver.find_element(By.ID, "filter")
        category = self.params.get("category", "Filing - Other/Miscellaneous")
        dropdown.find_element(By.XPATH, f"//option[. = '{category}']").click()

        console.print(f"Selected {category}")

        # Wait until the "type" dropdown is available
        sleep(3)

        dropdown = self.driver.find_element(By.ID, "type")
        sub_category = self.params.get(
            "sub_category", "Entry of Appear, Arrgnmnt Wavr & Not Guilty Plea"
        )
        dropdown.find_element(
            By.XPATH,
            f"//option[. = '{sub_category}']",
        ).click()

        console.print(f"Selected {sub_category}")

        sleep(3)
        # 17 | click | id=documentData |

        # Upload the file to the input in documentData
        self.driver.find_element(By.ID, "documentData").send_keys(
            filepath_document
        )

        console.print("Uploaded the file")

        # 19 | click | id=documentTitle |
        self.driver.find_element(By.ID, "documentTitle").click()

        # 20 | type | id=documentTitle | Entry of Appear, Arrgnmnt Wavr & Not Guilty Plea
        document_title = self.params.get(
            "template_title",
            "Entry of Appear, Arrgnmnt Wavr & Not Guilty Plea",
        )
        self.driver.find_element(By.ID, "documentTitle").send_keys(
            document_title
        )

        console.print("Added the document title")
        # 21 | click | id=addDoc |
        self.driver.find_element(By.ID, "addDoc").click()

        # Wait until the file is uploaded
        sleep(3)
        # 22 | click | id=continue |
        self.driver.find_element(By.ID, "continue").click()

        console.print("Clicked continue")

        # 24 | click | css=.redactionConfirmation |
        self.driver.find_element(
            By.CSS_SELECTOR, ".redactionConfirmation"
        ).click()

        console.print("Clicked redaction confirmation")

        self.driver.find_element(By.ID, "continue").click()
        console.print("Fully submitted the document")

        return {
            "case_number": case_number,
            "document_path": filepath_document,
            "status": "success",
        }


if __name__ == "__main__":
    connector = CaseNetWebConnector()
    case_number = "211182962"
    filepath = "./211182962_1_EOA_Mahmud_filled.pdf"

    try:
        connector.submit_document(
            filepath_document=filepath, case_number=case_number
        )
    except Exception as e:
        print(e)
    finally:
        connector.teardown()
