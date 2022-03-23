import datetime
import signal
import os
import random
import sys
from time import sleep
import pytz

import typer
from halo import Halo

import config
from core.cases import get_case_datails, get_verified_link, \
    get_lead_single_been_verified
from loader.config import ConfigLoader
from loader.leads import CaseNet
from scrapers.beenverified import BeenVerifiedScrapper


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

    while not killer.kill_now:
        tz = pytz.timezone('US/Central')
        date = str(datetime.datetime.now(tz).date())
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
                        results = get_case_datails(case_id)
                        spinner.succeed(
                            f"Succeeded to get details for case "
                            f"{case_id}")
                        year_of_birth = results['parties'].split(
                            "Year of Birth: ")
                        if len(year_of_birth) > 1:
                            try:
                                year_of_birth = int(year_of_birth[-1])
                            except Exception:
                                year_of_birth = None
                        name = results['parties'].split(", Defendant")
                        first_name, last_name, link = get_verified_link(
                            name, year_of_birth
                        )
                        try:
                            data = scrapper.retrieve_information(link)
                        except Exception as e:
                            spinner.fail(
                                f"Failed to retrieve information for case from beenverified"
                                f"{case_id}")
                        spinner.succeed(
                            "Retrieve data from BeenVerified finished "
                            "successfully")
                        cases.add(case_id)
                        sleep(random.randint(1, 10))

        except Exception as e:
            spinner.fail("Retrieve data process failed")
            print(e)
            sleep(random.randint(1, 10))
        except BaseException as e:
            spinner.fail("Retrieve data process failed")
            print(e)
            sleep(random.randint(1, 10))

    scrapper.teardown()


if __name__ == "__main__":
    app()
