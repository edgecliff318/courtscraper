import logging
from datetime import datetime

from src.core.config import get_settings
from src.scrapers.beenverified import BeenVerifiedScrapper
from src.scrapers.missouri import ScraperMOCourt

settings = get_settings()

logger = logging.Logger(__name__)


def get_case_details(case_id):
    case = {"case_number": case_id}
    scrapper = ScraperMOCourt()
    results = scrapper.get_case_detail(case)
    return results


def get_lead_single_been_verified(link):
    scrapper = BeenVerifiedScrapper(cache=True)
    try:
        data = scrapper.retrieve_information(link)
    except Exception as e:
        logger.error(e)
        scrapper.teardown()
        raise e
    finally:
        scrapper.teardown()
    return data


def get_verified_link(name, year_of_birth):
    first_name = None
    last_name = None
    middle_name = None
    if len(name) > 1:
        name = name[0]
        try:
            first_name = " ".join(name.split(", ")[1:])
            r = first_name.split(" ")
            if len(r) >= 2:
                first_name = r[0]
                middle_name = r[1]
            else:
                middle_name = ""
            last_name = " ".join(name.split(", ")[:1])
        except Exception:
            first_name = None
            last_name = None

    def get_beenverified_link(
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
        # if middle_name is not None:
        #    url += f"mn={middle_name}&"
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

    return (
        first_name,
        last_name,
        get_beenverified_link(
            first_name, last_name, middle_name, year_of_birth
        ),
    )
