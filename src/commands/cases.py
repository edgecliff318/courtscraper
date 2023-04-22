import datetime
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

    for day in range(-settings.start_date, -settings.end_date):
        date = str((datetime.datetime.now(tz) + Day(day)).date())
        for court in courts:
            console.log(f"Processing {court.name} ({court.code})")
            cases_ignore = cases_service.get_cases(
                court_code_list=court.code,
                start_date=date,
                end_date=date,
            )
            cases_imported = case_net.get_cases(
                court=court,
                case_type=case_type,
                date=date,
                cases_ignore=[case.case_id for case in cases_ignore],
            )
            console.log(f"Succeeded to retrieve " f"{len(cases_imported)}")
            for case in cases_imported:
                try:
                    case_parsed = cases_model.Case.parse_obj(case)
                    cases_service.insert_case(case_parsed)
                except Exception as e:
                    console.log(f"Failed to parse case {case} - {e}")
                try:
                    lead_parsed = leads_model.Lead.parse_obj(case)
                    leads_service.insert_lead(lead_parsed)
                except Exception as e:
                    console.log(f"Failed to parse lead {case} - {e}")


if __name__ == "__main__":
    typer.run(retrieve_cases)
