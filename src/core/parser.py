import datetime
import logging
import re

import pandas as pd
from commonregex import CommonRegex
from google.cloud import vision

logger = logging.Logger(__name__)


class TicketAnalyzer:
    def __init__(self, input_file_path, output_file_path):
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path

    def process(self):
        client = vision.ImageAnnotatorClient()
        logger.info(f"Processing {self.input_file_path}")
        with open(self.input_file_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        response = client.text_detection(image=image)
        texts = response.text_annotations

        output = ""

        for text in texts:
            output += '\n"{}"'.format(text.description)

            vertices = [
                "({},{})".format(vertex.x, vertex.y)
                for vertex in text.bounding_poly.vertices
            ]

        with open(self.output_file_path, "w") as text_file:
            logger.info(f"Saving the output file to {self.output_file_path}")
            text_file.write(output)

        if response.error.message:
            raise Exception(
                "{}\nFor more info on error messages, check: "
                "https://cloud.google.com/apis/design/errors".format(
                    response.error.message
                )
            )

        return self.extract(output)

    def get_case_id(self, output):
        client_name = re.search(r"\d{9}", output)[0]
        return client_name

    def get_state(self, output):
        state = re.search(
            r"(?<=STATE OF ).*?(?=\n)", output, flags=re.IGNORECASE
        ).group(0)
        return state

    def get_court_type(self, output):
        court_type = re.search(
            r"(?<=IN THE ).*?(?= COURT OF)", output, flags=re.IGNORECASE
        ).group(0)
        return court_type

    def get_offense(self, output):
        offense = re.search(
            r"(?<=BELIEF ARE AS FOLLOWS:\n)(.|\n)*(?=O Subject taken into "
            r"custody)",
            output,
            flags=re.IGNORECASE,
        ).group(0)

        return offense

    def _get_speeds(self, output):
        speeds = re.search(
            r"(?<=STATIONARY RADAR)(.|\n)*(?=MPH MOVING RADAR)",
            output,
            flags=re.IGNORECASE,
        ).group(0)
        l = []
        for s in speeds.split("\n"):
            s_parsed = re.search(r"\d{2,3}", s)
            if s_parsed:
                l.append(s_parsed.group(0))
        return l

    def get_ticket_speed(self, output):
        l = self._get_speeds(output)
        return l[0]

    def get_ticket_posted_speed_limit(self, output):
        l = self._get_speeds(output)
        return l[1]

    def _get_dates(self, output):
        parsed_text = CommonRegex(output)
        parsed_dates = []
        for e in parsed_text.dates:
            try:
                parsed_dates.append(pd.to_datetime(e))
            except Exception:
                continue
        return parsed_dates

    def get_client_birthdate(self, output):
        reduced_search = re.search(
            r"(?<=DATE OF BIRTH)(.|\n)*(?=DRIVER)", output, flags=re.IGNORECASE
        ).group(0)
        return min(self._get_dates(reduced_search)).strftime("%B %d, %Y")

    def get_court_time(self, output):
        reduced_search = re.search(
            r"(?<=\(DATE\))(.|\n)*(?=WITHIN CITY)", output, flags=re.IGNORECASE
        ).group(0)
        return max(self._get_dates(reduced_search)).strftime("%B %d, %Y")

    def _get_court_address(self, output):
        address = ",,"

        for e in (
            re.search(
                r"(?<=COURT ADDRESS \(Street, City, Zip\)\n)(.|\n)*("
                r"?=\nCOURT DATE)",
                output,
                flags=re.IGNORECASE,
            )
            .group(0)
            .split("\n")
        ):
            if "," in e:
                address = e

        address = address.split(",")
        zip, city, street = "", "", ""
        if address:
            zip = address.pop()
        if address:
            city = address.pop()
        if address:
            street = address.pop()

        return street, city, zip

    def get_court_phone(self, output):
        details = (
            re.search(
                r"(?<=COURT PHONE NO.\n)(.|\n)*(?=I, KNOWING)",
                output,
                flags=re.IGNORECASE,
            )
            .group(0)
            .split("\n")
        )

        for d in details:
            if "(" in d:
                return d
        return ""

    def get_court_city(self, output):
        street, city, zip = self._get_court_address(output)
        return city

    def get_client_name(self, output):
        return re.search(
            r"(?<=MIDDLE\)\n)(.|\n)*(?=\nSTREET)", output, flags=re.IGNORECASE
        ).group(0)

    def get_client_driver_license(self, output):
        driver_license = re.search(
            r"(?<=LIC. NO.\n).*?(?=\n)", output, flags=re.IGNORECASE
        ).group(0)
        if len(driver_license) <= 4:
            driver_license = (
                re.search(
                    r"(?<=\nCDL\nSTATE\n).*?(?=\nO)",
                    output,
                    flags=re.IGNORECASE,
                )
                .group(0)
                .replace(" ", "")
            )
        return driver_license

    def get_court_jurisdiction(self, output):
        return re.search(
            r"(?<=IN THE CIRCUIT COURT OF\n).*?(?=\nCOUNTY)",
            output,
            flags=re.IGNORECASE,
        ).group(0)

    def get_current_date(self, output):
        return datetime.datetime.now().strftime("%B %d, %Y")

    def extract(self, output):
        results = {}
        attributes_list = [
            "client_name",
            "case_id",
            "state",
            "court_type",
            "court_city",
            "court_jurisdiction",
            "court_phone",
            "court_time",
            "client_driver_license",
            "client_birthdate",
            "offense",
            "ticket_speed",
            "ticket_posted_speed_limit",
            "current_date",
        ]
        for attribute in attributes_list:
            if hasattr(self, f"get_{attribute}"):
                try:
                    results[attribute.replace("_", "-")] = getattr(
                        self, f"get_{attribute}"
                    )(output)
                except Exception:
                    logger.info(
                        f"A problem occurred while trying to extract "
                        f"{attribute} from {output}"
                    )

        return results
