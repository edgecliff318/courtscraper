import json
import logging
import random
import re
import time
from pathlib import Path

from pdf2image.pdf2image import convert_from_path
from rich.console import Console

from src.core.config import get_settings
from src.db import bucket
from src.loader.tickets import TicketParser
from src.models import cases as cases_model
from src.models import leads as leads_model
from src.services import cases as cases_service
from src.services import leads as leads_service
from src.services import settings as settings_service

settings = get_settings()
console = Console()

logger = logging.Logger(__name__)


class ScraperBase:
    """Base class which describes the interface that all scrapers should implement.

    Also contains some utility methods.
    """

    def __init__(self, username=None, password=None, url=None) -> None:
        self.username = username
        self.password = password
        self.url = url
        self._GLOBAL_SESSION = None
        self.scraper_service = settings_service.ScrapersService()
        self.scraper_settings = self.scraper_service.get_single_item(
            self.__class__.__name__
        )
        self.state = self.scraper_settings.state or {}

    def update_state(self):
        """Update the scraper settings."""
        console.log(f"Updating state for {self.__class__.__name__}")
        self.scraper_service.patch_item(
            self.__class__.__name__, {"state": self.state}
        )

    def scrape(self, search_parameters):
        """
        Entry point for lambda. Query event should look like this:

        {
            lastName: "Jones",
            firstName: "David",
            dob: "1/31/1987"
        }

        https://<endpoint>?queryStringParameters
        """

        raise NotImplementedError()

    def save_json(self, data, case_number):
        """Save the json data to a file."""
        filepath = settings.DATA_PATH.joinpath(f"{case_number}.json")
        with open(filepath, "w") as f:
            json.dump(data, f)
        return filepath

    def convert_to_png(self, ticket_filepath, case_number):
        images = convert_from_path(ticket_filepath)
        if images:
            image = images[0]  # Take only the first page
            docket_image_filepath = settings.DATA_PATH.joinpath(
                f"{case_number}.png"
            )
            image.save(docket_image_filepath, "PNG")
            return str(docket_image_filepath)
        return None

    def parse_ticket(self, ticket_filepath, case_number):
        try:
            ticket_parser = TicketParser(
                filename=None,
                input_file_path=ticket_filepath,
                output_file_path=settings.DATA_PATH.joinpath(
                    f"{case_number}.json"
                ),
            )
            ticket_parsed = ticket_parser.parse()
            return {
                e.get("field-id"): e.get("field-value")
                for e in ticket_parsed.get("form", [])
            }
        except Exception as e:
            logger.error(e)
            return {"error": "Failed to parse ticket"}

    def upload_file(self, filepath):
        filename = filepath.split("/")[-1]
        blob = bucket.blob(filename)
        blob.upload_from_filename(filepath)
        return filename

    @staticmethod
    def ensure_folder(folder_path):
        """
        Function to create a folder if path doesn't exist
        """
        Path(folder_path).mkdir(parents=True, exist_ok=True)

    def download(self, link, filetype="pdf"):
        """Download the pdf file from the given link."""
        self.ensure_folder(settings.DATA_PATH)
        filepath = settings.DATA_PATH.joinpath(
            link.split("/")[-1] + "." + filetype.lower()
        )
        with open(filepath, "wb") as f:
            r = self.GLOBAL_SESSION.get(link, stream=True)
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()
        logger.info(f"File saved to {filepath}")
        return str(filepath)

    def sleep(self):
        """Sleeps for a random amount of time between requests"""
        # Show a message with an emoji for waiting time
        waiting_time = random.randint(1, 3)
        console.print(
            f"Waiting for {waiting_time} seconds :hourglass:", style="bold"
        )
        time.sleep(waiting_time)

    def to_snake(self, s):
        return re.sub("([A-Z]\w+$)", "_\\1", s).lower()

    def t_dict(self, d) -> dict:
        if isinstance(d, list):
            return [
                self.t_dict(i) if isinstance(i, (dict, list)) else i for i in d
            ]
        return {
            self.to_snake(a): self.t_dict(b)
            if isinstance(b, (dict, list))
            else b
            for a, b in d.items()
        }

    def check_if_exists(self, case_id):
        """Check if the case already exists in the database."""
        if cases_service.get_single_case(case_id) is not None:
            return True
        return False

    def insert_case(self, case, force_insert=False):
        """Insert the case into the database."""
        try:
            case_parsed = cases_model.Case.model_validate(case)
            if self.check_if_exists(case_parsed.case_id) and not force_insert:
                console.log(f"Case {case_parsed.case_id} already exists")
                return
            cases_service.insert_case(case_parsed)
            console.log(f"Succeeded to insert case {case.get('case_id')}")
        except Exception as e:
            # Save the case in a file for a manual review
            self.ensure_folder("cases_to_review")
            with open(
                f"cases_to_review/{case.get('case_id')}.json",
                "w",
            ) as f:
                # Transform PosixPath to path in the dict case
                json.dump(case, f, default=str)

            console.log(f"Failed to parse case {case} - {e}")
            raise e

    def insert_lead(self, case):
        """Insert the lead into the database."""
        try:
            lead_parsed = leads_model.Lead.model_validate(case)
            lead_loaded = leads_service.get_single_lead(lead_parsed.case_id)
            if lead_loaded is None:
                leads_service.insert_lead(lead_parsed)
            console.log(f"Succeeded to insert lead for {case.get('case_id')}")
        except Exception as e:
            console.log(f"Failed to parse lead {case} - {e}")
            raise e
