import asyncio
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
from src.scrapers.arkansas import ArkansasScraper
from src.scrapers.broward import BrowardScraper
from src.scrapers.il_cook import IlCook
from src.scrapers.indiana import IndianaScraper
from src.scrapers.kansas import KansasScraper
from src.scrapers.ks_johnson import KSJohnson
from src.scrapers.minnesota import MinnesotaScraper
from src.scrapers.mo_mshp import MOHighwayPatrol
from src.scrapers.north_carolina import NorthCarolinaScraper
from src.scrapers.north_carolina_superior import ScraperNCSuperior
from src.scrapers.oklahoma import OklahomaScraper
from src.scrapers.fl_palm_beach import PalmBeachScraper
from src.scrapers.tx_harris import TXHarrisCountyScraper
from src.scrapers.tx_travis import ScraperTXTravisSuperior
from src.scrapers.va_courts import VirginiaScraper
from src.scrapers.west_virginia import WestVirginiaScraper
from src.scrapers.maryland_general import MDGeneralScraper
from src.services import cases as cases_service
from src.services import leads as leads_service
from src.services.courts import get_courts
from src.services.settings import ScrapersService, get_account, get_settings

console = Console()

logger = logging.getLogger()


def retrieve_cases_mo_casenet(case_type="Traffic%2FMunicipal"):
    courts = get_courts()
    settings = get_settings("main")
    case_net_account = get_account("case_net_missouri_sam")

    tz = pytz.timezone("US/Central")

    console.log(
        f"Start date: {settings.start_date}, " f"End date: {settings.end_date}"
    )

    case_net = CaseNet(
        url=case_net_account.url,
        username=case_net_account.username,
        password=case_net_account.password,
    )

    court_filter = {
        "Criminal": ["CAS", "CLY", "JAK", "JON", "LAF", "RAY", "PLA"]
    }

    for day in range(-settings.end_date, -settings.start_date - 1, -1):
        date = str((datetime.datetime.now(tz) + Day(day)).date())
        console.log(f"Processing date {date}")
        for court in courts:
            if (
                court.code == "MEYER"
                or court.code == "TONI"
                or court.code == "temp"
                or court.state != "MO"
                or court.code == "IL_COOK"
            ):
                continue

            if court_filter.get(case_type) is not None:
                if court.id not in court_filter.get(case_type, []):
                    continue
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
                        case_parsed = cases_model.Case.model_validate(case)
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
                        lead_parsed = leads_model.Lead.model_validate(case)
                        lead_loaded = leads_service.get_single_lead(
                            lead_parsed.case_id
                        )
                        if lead_loaded is None:
                            if case_type == "Criminal":
                                lead_parsed.status = "prioritized"
                            leads_service.insert_lead(lead_parsed)
                    except Exception as e:
                        console.log(f"Failed to parse lead {case} - {e}")


def retrieve_cases_mo_mshp():
    # Start date
    end_date = datetime.datetime.now() + datetime.timedelta(days=1)

    # End date = start - 15 days
    start_date = end_date - datetime.timedelta(days=15)

    cases_imported = cases_service.get_cases(
        start_date=start_date, end_date=end_date, source="mo_mshp"
    )

    scraper = MOHighwayPatrol()
    cases_imported = scraper.get_cases(cases_filter=cases_imported)

    for case in cases_imported:
        # Insert the case in the cases table
        try:
            case_parsed = cases_model.Case.model_validate(case)
            cases_service.insert_case(case_parsed)
            console.log(f"Succeeded to insert case {case.get('case_id')}")
        except Exception as e:
            # Save the case in a file for a manual review
            with open(
                f"cases_to_review/{case.get('case_id')}.json",
                "w",
            ) as f:
                # Transform PosixPath to path in the dict case
                json.dump(case, f, default=str)

            console.log(f"Failed to parse case {case} - {e}")

        # Insert the lead in the leads table:
        try:
            lead_parsed = leads_model.Lead.model_validate(case)
            lead_loaded = leads_service.get_single_lead(lead_parsed.case_id)
            if lead_loaded is None:
                leads_service.insert_lead(lead_parsed)
                console.log(
                    f"Succeeded to insert lead for {case.get('case_id')}"
                )
        except Exception as e:
            console.log(f"Failed to parse lead {case} - {e}")


def retrieve_cases_il_cook(refresh_courts=None) -> None:
    # (start_date : str, end_date: str , email: str, password: str, search_by: str, search_judicial_officer: str):
    """
    Scrap the casenet website
    """
    # Get the configuration from Firebase
    console.log("Retrieving the configuration from Firebase")
    account = get_account("il_cook_tyler")

    if account.start_date is None:
        account.start_date = 0

    if account.end_date is None:
        account.end_date = 1

    # Initiate the scrapper
    for shift_days in range(account.start_date, account.end_date):
        console.log(f"Processing date {shift_days}")
        target_date = datetime.datetime.now() + datetime.timedelta(
            days=shift_days
        )

        # If not business day or a holiday, skip
        if target_date.weekday() > 4:
            continue

        scraper = IlCook(
            email=account.email,
            password=account.password,
            start_date=target_date.strftime("%m/%d/%Y"),
            end_date=target_date.strftime("%m/%d/%Y"),
        )

        # Get the cases
        asyncio.run(scraper.main())


def retrieve_cases_tx_harris():
    console.log("TX Harris County Scraper")
    txscraper = TXHarrisCountyScraper()

    console.log("Retrieving the configuration from Firebase")
    txscraper_config = ScrapersService().get_single_item("TXHarrisCounty")

    start_date = datetime.datetime.now() + datetime.timedelta(
        days=txscraper_config.start_date
    )
    end_date = datetime.datetime.now() + datetime.timedelta(
        days=txscraper_config.end_date
    )

    console.log(f"Start date: {start_date}, End date: {end_date}")

    txscraper.scrape(
        {
            "start_date": start_date.strftime("%m/%d/%Y"),
            "end_date": end_date.strftime("%m/%d/%Y"),
        }
    )


def retrieve_cases_arkansas():
    console.log("Arkansas Scraper")
    arkansasscraper = ArkansasScraper()
    console.log("Retrieving the configuration from Firebase")
    arkansasscraper.scrape()


def retrieve_cases_indiana():
    console.log("Indiana State Scraper")
    indianascraper = IndianaScraper()
    filed_date = "04/12/2024"
    search_parameters = {"filed_date": filed_date}
    indianascraper.scrape(search_parameters)


def retrieve_cases_oklahoma():
    console.log("Oklahoma Scraper")
    oklahomascraper = OklahomaScraper()
    filed_date = "03/25/2024"
    oklahomascraper.scrape({"filed_date": filed_date})


def retrieve_cases_tx_travis():
    console.log("Travis County, Tx State Scraper")
    travissuperiorscraper = ScraperTXTravisSuperior()
    search_parameters = {
        "firstName": "John",
        "lastName": "Washington",
        "dob": None,
    }
    travissuperiorscraper.scrape(search_parameters)


def retrieve_cases_nc_superior():
    console.log("NC Superior Scraper")
    ncsuperiorscraper = ScraperNCSuperior()
    search_parameters = {
        "firstName": "Adam",
        "lastName": "Smith",
        "dob": "12/19/1967",
    }
    ncsuperiorscraper.scrape(search_parameters)


async def retrieve_cases_minnesota():
    console.log("Minnesota State Scraper")
    minnesotascraper = MinnesotaScraper()
    search_parameters = {"case_id": "27-VB-24-69261"}
    await minnesotascraper.scrape(search_parameters)


async def retrieve_cases_fl_palm_beach():
    console.log("Palm Beach County Scraper")
    palmbeachscraper = FLPalmBeachScraper()
    await palmbeachscraper.scrape()


async def retrieve_cases_broward():
    console.log("Broward County, Florida Scraper")
    browardscraper = BrowardScraper()
    await browardscraper.scrape()


async def retrieve_cases_virginia_district():
    console.log("Virginia State District Court Scraper")
    va_district_scraper = VADistrictScraper()
    await va_district_scraper.scrape()


async def retrieve_cases_west_virginia():
    console.log("West Virginia Scraper")
    westvirginiascraper = WestVirginiaScraper()
    name = "AB"
    await westvirginiascraper.scrape({"name": name})


async def retrieve_cases_kansas():
    console.log("Kansas Scraper")
    kansasscraper = KansasScraper()
    search_parameters = {
        "user_name": "Smahmudlaw@gmail.com",
        "password": "Shawn1993!",
    }
    await kansasscraper.scrape(search_parameters)


async def retrieve_cases_north_carolina():
    console.log("North Carolina State Scraper")
    northcarolinascraper = NorthCarolinaScraper()
    await northcarolinascraper.scrape()


async def retrieve_cases_minnesota():
    console.log("Minnesota State Scraper")
    minnesotascraper = MinnesotaScraper()
    await minnesotascraper.scrape()

async def retrieve_cases_maryland_general():
    console.log("Maryland State General Court Scraper")
    md_general_scraper = MDGeneralScraper()
    await md_general_scraper.scrape()

async def retrieve_cases_ks_johnson():
    console.log("Johnson County, KS State Scraper")
    johnsonscraper = KSJohnson()
    search_parameters = {"user_name": "30275", "password": "TTDpro2024TTD!"}
    await johnsonscraper.scrape(search_parameters)

def retrieve_cases(source="mo_case_net"):
    """
    Scrap the casenet website
    """
    if source == "mo_case_net":
        console.log("MO Case Net Scraper")
        retrieve_cases_mo_casenet()
    elif source == "mo_mshp":
        console.log("MO Highway Patrol Scraper")
        retrieve_cases_mo_mshp()
    elif source == "il_cook":
        console.log("Cook County, IL Scraper")
        retrieve_cases_il_cook()
    elif source == "mo_case_net_criminal":
        console.log("MO Case Net Scraper - Criminal")
        retrieve_cases_mo_casenet("Criminal")
    elif source == "tx_harris":
        console.log("Harris County, Texas Scraper")
        retrieve_cases_tx_harris()
    elif source == "arkansas":
        console.log("Arkansas State Scraper")
        retrieve_cases_arkansas()
    elif source == "oklahoma":
        console.log("Oklahoma State Scraper")
        retrieve_cases_oklahoma()
    elif source == "tx_travis":
        console.log("Travis County, Texas State Scraper")
        retrieve_cases_tx_travis()
    elif source == "nc_superior":
        console.log("Travis County, Texas State Scraper")
        retrieve_cases_nc_superior()
    elif source == "broward":
        console.log("Broward County Scraper")
        asyncio.run(retrieve_cases_broward())

    elif source == "indiana":
        console.log("Indiana Scraper")
        asyncio.run(retrieve_cases_indiana())
    elif source == "minnesota":
        console.log("Minnesota Scraper")
        asyncio.run(retrieve_cases_minnesota())
    elif source == "maryland_general":
        console.log("Maryland General Scraper")
        asyncio.run(retrieve_cases_maryland_general())
    elif source == "north_carolina":
        console.log("North Carolina Scraper")
        asyncio.run(retrieve_cases_north_carolina())
    elif source == "kansas":
        console.log("Kansas State Scraper")
        asyncio.run(retrieve_cases_kansas())
    elif source == "ks_johnson":
        console.log("Johnson County, Kansas State Scraper")
        asyncio.run(retrieve_cases_ks_johnson())
    elif source == "west_virginia":
        console.log("West_Virginia State Scraper")
        asyncio.run(retrieve_cases_west_virginia())
    elif source == "fl_palm_beach":
        console.log("FL Palm Beach Scraper")
        asyncio.run(retrieve_cases_fl_palm_beach())

if __name__ == "__main__":
    typer.run(retrieve_cases)
