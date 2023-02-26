import datetime
import logging
import os
import json
import random
import signal
import sys
from time import sleep

import pytz
import requests
import typer
from pandas.tseries.offsets import Day
from rich.console import Console
from rich.logging import RichHandler

from src.core.config import get_settings
from src.core.cases import get_case_datails, get_verified_link
from src.loader.config import ConfigLoader
from src.loader.leads import CaseNet
from src.scrapers.beenverified import BeenVerifiedScrapper

settings = get_settings()

# Logging configuration
logger = logging.getLogger()
rich_handler = RichHandler()
file_handler = logging.FileHandler(filename="core.log")
rich_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
)
rich_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(rich_handler)


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True


app = typer.Typer()

sys.setrecursionlimit(10000)


@app.command()
def retrieve():
    """
    Retrieve historical data for a given symbol
    """
    console = Console()
    console.print(":rocket: [bold]Welcome to the BeenVerified Scraper[/bold] :rocket:")

    killer = GracefulKiller()

    config_loader = ConfigLoader(path=os.path.join(settings.CONFIG_PATH, "config.json"))

    court_code_list = [
        c for c in config_loader.load()["courts"] if c.get("enabled", False)
    ]
    cases = set()

    scrapper = BeenVerifiedScrapper(cache=False)
    console.print(f"Logged to BeenVerified")

    while True:
        tz = pytz.timezone("US/Central")
        for day in range(-85, -1):
            date = str((datetime.datetime.now(tz) + Day(day)).date())

            console.log(f"Retrieving cases for {date}")

            try:
                for case_type in ("Traffic%2FMunicipal",):
                    for court in court_code_list:
                        court_code = court.get("value")
                        court = config_loader.get_court_details(court_code)
                        console.log(f"Retrieving cases for {court.get('label')}")

                        case_net = CaseNet(
                            url=settings.CASE_NET_URL,
                            username=settings.CASE_NET_USERNAME,
                            password=settings.CASE_NET_PASSWORD,
                        )
                        courts_data = case_net.get_leads(
                            court_code, court.get("countycode"), date, case_type
                        )
                        # Log the success message

                        console.log(
                            f"Succeeded to retrieve "
                            f"{len(courts_data.get('data', []))}"
                        )

                        for case in courts_data.get("data", []):
                            case_id = case.get("caseNumber")
                            if case_id in cases:
                                continue

                            case_info = {
                                "case_id": case_id,
                                "case_type": case_type,
                                "court_code": court_code,
                                "court_name": court.get("label"),
                                "case_date": date,
                                "first_name": "",
                                "last_name": "",
                                "been_verified": False,
                                "age": "",
                                "year_of_birth": "",
                                "charges": "",
                                "details": "",
                                "email": "",
                            }

                            cases.add(case_id)
                            first_name = None
                            last_name = None
                            year_of_birth = None

                            try:
                                results = get_case_datails(case_id)
                                case_info["charges"] = (
                                    results.get("charges", {})
                                    .get("Charge/Judgment", {})
                                    .get("Description")
                                )
                                case_info["casenet"] = results
                            except Exception as e:
                                console.log(
                                    f"Failed to retrieve information for case from CaseNet "
                                    f"{case_id} - error {e}"
                                )
                                console.log(
                                    f"Failed to retrieve information for case from CaseNet "
                                    f"{case_id} - error {e}"
                                )
                                raise e
                            console.log(
                                f"Succeeded to get details for case " f"{case_id}"
                            )

                            try:
                                year_of_birth = results["parties"].split(
                                    "Year of Birth: "
                                )
                                if len(year_of_birth) > 1:
                                    try:
                                        year_of_birth = int(
                                            year_of_birth[-1].split("\n")[-1]
                                        )
                                        age = datetime.date.today().year - year_of_birth
                                        case_info["age"] = age
                                    except Exception as e:
                                        console.log(
                                            f"Failed to get age for case {case_id} - error {e}"
                                        )
                                        year_of_birth = None
                                name = results["parties"].split(", Defendant")
                                first_name, last_name, link = get_verified_link(
                                    name, year_of_birth
                                )
                                case_info["first_name"] = first_name
                                case_info["last_name"] = last_name
                                case_info["year_of_birth"] = year_of_birth
                                data = scrapper.retrieve_information(link)
                                case_info["been_verified"] = True
                                case_info["phone"] = data.get("phone")
                                case_info["details"] = data.get("details")
                                case_info["email"] = data.get("email")

                                console.log(
                                    "Retrieve data from BeenVerified finished "
                                    "successfully"
                                )
                                if data.get("error", True):
                                    raise Exception(
                                        "An issue happened with beenverified"
                                    )

                                case_info = json.loads(
                                    json.dumps(
                                        case_info,
                                        default=lambda o: "<not serializable>",
                                    )
                                )
                                requests.post(
                                    settings.REMOTE_UPDATE_URL, json=case_info
                                )
                            except Exception as e:
                                console.print(
                                    f"Failed to retrieve information for case from BeenVerified "
                                    f"{case_id}",
                                    style="bold red",
                                )
                                logger.debug(
                                    f"Failed to retrieve information for case from BeenVerified "
                                    f"{case_id} - error {e}"
                                )
                                console.print_exception(show_locals=True)

                            sleep(random.randint(40, 70))

            except Exception as e:
                console.print(
                    f"Retrieve data process failed - error {e}", style="bold red"
                )
                logger.debug(f"Retrieve data process failed - error {e}")
                console.print_exception(show_locals=True)
                with console.status("Retrying in few seconds ..."):
                    sleep(random.randint(1, 10))

            with console.status("Sleep for a long time priod ..."):
                sleep(random.randint(1000, 2000))

    scrapper.teardown()


if __name__ == "__main__":
    app()
