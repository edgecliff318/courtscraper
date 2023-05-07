import json
import logging
import random
import re
import time

import requests
from pdf2image.pdf2image import convert_from_path
from rich.console import Console

from src.core.config import get_settings
from src.loader.tickets import TicketParser

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
            return docket_image_filepath
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
        files = {"file": open(filepath, "rb")}
        # TODO: #10 Protect the upload url with a secret key
        response = requests.post(
            settings.REMOTE_DATA_UPLOAD_URL,
            files=files,
            params={"api_key": settings.API_KEY},
        )
        if response.status_code != 200:
            logger.error(
                f"Error uploading file to remote" f" server : {response.text}"
            )
            console.log(
                f"Error uploading file to remote" f" server : {response.text}"
            )
            raise Exception(
                f"Error uploading file to remote server : {response.text}"
            )

    def download(self, link, filetype="pdf"):
        """Download the pdf file from the given link."""
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
        waiting_time = random.randint(5, 10)
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
