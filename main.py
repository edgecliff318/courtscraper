import datetime
import logging
import signal
import os
import random
import sys
from time import sleep
import pytz
import requests

import typer
from halo import Halo

import config
from core.cases import get_case_datails, get_verified_link, \
    get_lead_single_been_verified
from loader.config import ConfigLoader
from loader.leads import CaseNet
from scrapers.beenverified import BeenVerifiedScrapper
from pandas.tseries.offsets import BDay


filehandler = logging.FileHandler("app.log")
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logging.RootLogger(level=config.logging_level).addHandler(filehandler)


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
    spinner = Halo(
        text="Starting the retrieve data process ...",
        spinner="dots"
    )
    killer = GracefulKiller()

    config_loader = ConfigLoader(
        path=os.path.join(config.config_path, "config.json"))

    court_code_list = [
        c for c in config_loader.load()['courts']
        if c.get("enabled", False)
    ]
    cases = set()

    scrapper = BeenVerifiedScrapper(cache=False)
    spinner.succeed(f"Logged to BeenVerified")

    while True:
        tz = pytz.timezone('US/Central')
        date = str((datetime.datetime.now(tz) - BDay(1)).date())
        spinner.start()

        try:
            for case_type in ("Traffic%2FMunicipal", "Infraction"):
                for court in court_code_list:
                    court_code = court.get('value')
                    court = config_loader.get_court_details(court_code)
                    spinner.info(f"Retrieving cases for {court.get('label')}")

                    case_net = CaseNet(
                        url=config.case_net_url,
                        username=config.case_net_username,
                        password=config.case_net_password
                    )
                    courts_data = case_net.get_leads(
                        court_code, court.get("countycode"), date,
                        case_type
                    )
                    spinner.succeed(
                        f"Succeeded to retrieve "
                        f"{len(courts_data.get('data', []))}")

                    for case in courts_data.get('data', []):
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
                            "email": ""
                        }

                        cases.add(case_id)
                        first_name = None
                        last_name = None
                        year_of_birth = None

                        try:
                            results = get_case_datails(
                                case_id, session=case_net.session)
                            case_info["charges"] = results.get("charges", {}).get(
                                "Charge/Judgment", {}).get("Description")
                        except Exception as e:
                            spinner.fail(
                                f"Failed to retrieve information for case from CaseNet "
                                f"{case_id} - error {e}")
                            raise e
                        spinner.succeed(
                            f"Succeeded to get details for case "
                            f"{case_id}")

                        try:
                            year_of_birth = results['parties'].split(
                                "Year of Birth: ")
                            if len(year_of_birth) > 1:
                                try:
                                    year_of_birth = int(
                                        year_of_birth[-1].split("\n")[-1])
                                    age = datetime.date.today().year - year_of_birth
                                    case_info["age"] = age
                                except Exception as e:
                                    spinner.error(
                                        f"Failed to get age for case {case_id} - error {e}"
                                    )
                                    year_of_birth = None
                            name = results['parties'].split(", Defendant")
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

                            spinner.succeed(
                                "Retrieve data from BeenVerified finished "
                                "successfully"
                            )
                            if data.get("error", True):
                                raise Exception(
                                    "An issue happened with beenverified")
                            requests.post(
                                config.remote_update_url,
                                json=case_info
                            )
                        except Exception as e:
                            spinner.fail(
                                f"Failed to retrieve information for case from BeenVerified "
                                f"{case_id} - error {e}")

                        sleep(random.randint(40, 70))

        except Exception as e:
            spinner.fail(f"Retrieve data process failed - error {e}")
            sleep(random.randint(1, 10))
        sleep(random.randint(1000, 2000))

    scrapper.teardown()


if __name__ == "__main__":
    app()
