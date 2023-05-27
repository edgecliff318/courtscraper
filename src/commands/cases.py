import datetime
import json
import logging

import pytz
import typer
from pandas.tseries.offsets import Day
from rich.console import Console

from src.loader.leads import CaseNet
from src.models import cases as cases_model
from src.models import leads as leads_model
from src.services import cases as cases_service
from src.services import leads as leads_service
from src.services.courts import get_courts
from src.services.settings import get_account, get_settings

console = Console()

logger = logging.getLogger()


def retrieve_cases():
    """
    Scrap the casenet website
    """

    courts = get_courts()
    settings = get_settings("main")
    case_net_account = get_account("case_net_missouri")

    tz = pytz.timezone("US/Central")

    console.log(
        f"Start date: {settings.start_date}, " f"End date: {settings.end_date}"
    )

    case_type = "Traffic%2FMunicipal"

    case_net = CaseNet(
        url=case_net_account.url,
        username=case_net_account.username,
        password=case_net_account.password,
    )

    for day in range(-settings.end_date, -settings.start_date - 1, -1):
        date = str((datetime.datetime.now(tz) + Day(day)).date())
        console.log(f"Processing date {date}")
        for court in courts:
            cases_retrieved = []
            while True:
                console.log(f"Processing {court.name} ({court.code})")

                # Set start date at 00:00:00 and end date at 23:59:59
                start_date = datetime.datetime.strptime(date, "%Y-%m-%d")

                end_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                end_date = end_date.replace(hour=23, minute=59, second=59)

                cases_ignore = []
                cases_imported = case_net.get_cases(
                    court=court,
                    case_type=case_type,
                    date=date,
                    cases_ignore=[case.case_id for case in cases_ignore]
                    + cases_retrieved,
                )
                console.log(f"Succeeded to retrieve " f"{len(cases_imported)}")
                if not cases_imported:
                    console.log(
                        f"Retrieved all cases from {court.name} ({court.code})"
                    )
                    break
                else:
                    cases_retrieved += [
                        case.get("case_id") for case in cases_imported
                    ]
                for case in cases_imported:
                    # Reimport the module cases_model
                    # to avoid the error:
                    # TypeError: Object of type Case is not JSON serializable
                    # https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable

                    try:
                        case_parsed = cases_model.Case.parse_obj(case)
                        cases_service.insert_case(case_parsed)
                    except Exception as e:
                        # Save the case in a file for a manual review
                        with open(
                            f"cases_to_review/{date}_{court.code}_{case.get('case_id')}.json",
                            "w",
                        ) as f:
                            # Transform PosixPath to path in the dict case
                            json.dump(case, f, default=str)
                        console.log(f"Failed to parse case {case} - {e}")
                    try:
                        lead_parsed = leads_model.Lead.parse_obj(case)
                        lead_loaded = leads_service.get_single_lead(
                            lead_parsed.case_id
                        )
                        if lead_loaded is None:
                            leads_service.insert_lead(lead_parsed)
                    except Exception as e:
                        console.log(f"Failed to parse lead {case} - {e}")


if __name__ == "__main__":
    typer.run(retrieve_cases)
