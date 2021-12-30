import base64
import os
from urllib.parse import quote as urlquote

import config
from core.parser import TicketAnalyzer


class TicketsManager(object):
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def save(self, name, content):
        """Decode and store a file uploaded with Plotly Dash."""
        data = content.encode("utf8").split(b";base64,")[1]
        with open(os.path.join(self.folder_path, name), "wb") as fp:
            fp.write(base64.decodebytes(data))

    def list(self):
        """List the files in the upload directory."""
        files = []
        for filename in os.listdir(self.folder_path):
            path = os.path.join(self.folder_path, filename)
            if os.path.isfile(path):
                files.append(filename)
        return files

    def link(self, filename):
        """Create a Plotly Dash 'A' element that downloads a file from the
        app."""
        location = "/download/{}".format(urlquote(filename))
        return location


class TicketParser(object):
    def __init__(self, filename):
        self.filename = filename
        self.input_file_path = os.path.join(config.upload_path, filename)
        self.output_file_path = os.path.join(config.output_path, filename)

    def get_fields(self, results: dict):
        return [
            {
                "field-label": "Client Name",  # {CLIENT NAME} = DHRUV PATEL
                "field-value": results.get("client-name"),
                "field-id": "client-name"
            },
            {
                "field-label": "Case ID",  # {CASE #} = 703585940
                "field-value": results.get("case-id"),
                "field-id": "case-id"
            },
            {
                "field-label": "State",  # {STATE} = MISSOURI
                "field-value": results.get("state"),
                "field-id": "state"
            },
            {
                "field-label": "Court Type",  # {COURT TYPE} = CIRCUIT
                "field-value": results.get("court-type"),
                "field-id": "court-type"
            },
            {
                "field-label": "Court City",  # {COURT CITY} = WARRENTON
                "field-value": results.get("court-city"),
                "field-id": "court-city"
            },
            {
                "field-label": "Court Jurisdiction",  # {COURT JURISDICTION}
                # = WARREN COUNTY
                "field-value": results.get("court-jurisdiction"),
                "field-id": "court-jurisdiction"
            },
            {
                "field-label": "Court Phone",  # {COURT PHONE} = 6364653375
                "field-value": results.get("court-phone"),
                "field-id": "court-phone"
            },
            {
                "field-label": "Court Time",
                # {COURT DATE} = SEPTEMBER 28, 2021
                "field-value": results.get("court-time"),
                "field-id": "court-time"
            },
            {
                "field-label": "Client Birthdate",
                # {CLIENT BIRTHDATE} = SEPTEMBER 29, 1987
                "field-value": results.get("client-birthdate"),
                "field-id": "client-birthdate"
            },
            {
                "field-label": "Client Driver License",
                # {CLIENT DRIVERS LICENSE #} = 001A262004
                "field-value": results.get("client-driver-license"),
                "field-id": "client-driver-license"
            },
            {
                "field-label": "Offense",  # {OFFENSE} = Exceeded posted
                # speed limit (exceeded by 16 - 19 miles per hour)
                "field-value": results.get("offense"),
                "field-id": "offense"
            },
            {
                "field-label": "Speed at Time of Ticket",
                # {SPEED AT TIME OF TICKET} = 89
                "field-value": results.get("ticket-speed"),
                "field-id": "ticket-speed"
            },
            {
                "field-label": "Posted Speed Limit",
                "field-value": results.get("ticket-posted-speed-limit"),
                "field-id": "ticket-posted-speed-limit"
            },
            {
                "field-label": "Current Date",  # {CURRENT DATE} =
                # NOVEMBER 02, 2021
                "field-value": results.get("current-date"),
                "field-id": "current-date"
            },
        ]

    def parse(self):
        ticket_analyzer = TicketAnalyzer(
            input_file_path=self.input_file_path,
            output_file_path=self.output_file_path
        )
        results = ticket_analyzer.process()
        data = self.get_fields(results=results)
        return {
            "form": data,
            "image": self.input_file_path
        }
