import base64
import html.parser
import logging
from datetime import datetime

from bs4 import BeautifulSoup
from googleapiclient.discovery import build

from src.services.emails_auth import get_credentials

# Number of seconds the subscriber should listen for messages
TIMEOUT = 200000

logger = logging.getLogger(__name__)


class HTMLTextExtractor(html.parser.HTMLParser):
    def __init__(self):
        super(HTMLTextExtractor, self).__init__()
        self.result = []

    def handle_data(self, d):
        self.result.append(d)

    def get_text(self):
        return "".join(self.result)


def html_to_text(html):
    s = HTMLTextExtractor()
    s.feed(html)
    return s.get_text()


class GmailConnector(object):
    def __init__(self, user_id):
        self.renew = True
        self.user_id = user_id
        self.credentials = None

    @property
    def service(self):
        if self.credentials is None:
            self.credentials = get_credentials(user_id=self.user_id)

        service = build("gmail", "v1", credentials=self.credentials)
        return service

    def get_inbox_emails(self):
        try:
            emails = (
                self.service.users().messages().list(userId="me").execute()
            )

            messages = []

            def add(id, msg, err):
                # id is given because this will not be called in the same order
                if err:
                    print(err)
                else:
                    messages.append(msg)

            batch = self.service.new_batch_http_request()
            for message in emails.get("messages", []):
                batch.add(
                    self.service.users()
                    .messages()
                    .get(userId="me", id=message["id"]),
                    callback=add,
                )

            batch.execute()

            return [
                {
                    "id": message["id"],
                    "snippet": message["snippet"],
                    "payload": message["payload"],
                    "internalDate": message["internalDate"],
                }
                for message in messages
            ]

        except Exception as error:
            print("An error occurred: %s" % error)
            raise error

    def get_message(self, message_id):
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id)
                .execute()
            )
            headers = message["payload"]["headers"]

            message_time = datetime.fromtimestamp(
                int(message.get("internalDate")) / 1000
            )

            subject = [
                header["value"]
                for header in headers
                if header["name"] == "Subject"
            ][0]

            return {
                "subject": subject,
                "sender": [
                    header["value"]
                    for header in headers
                    if header["name"] == "From"
                ][0],
                "time": message_time,
            }

        except Exception as error:
            print("An error occurred: %s" % error)

    def get_email(self, email_id):
        try:
            email = (
                self.service.users()
                .messages()
                .get(userId="me", id=email_id)
                .execute()
            )
            return email

        except Exception as error:
            logger.error(
                f"An error occurred while retrieving {email_id}: {error}"
            )

    @staticmethod
    def get_email_html_body(email):
        body = email.get("payload", {}).get("body", {})

        final_body = base64.urlsafe_b64decode(
            body["data"].encode("utf-8")
        ).decode("utf-8")

        # Remove all the style
        soup = BeautifulSoup(final_body, "html.parser")

        # Extract the text body
        for script in soup(["script", "style"]):
            script.extract()

        text_body = soup.get_text()

        # Remove all the new lines and \u200c and similar characters
        text_body = text_body.encode("ascii", "ignore").decode("utf-8")

        # Remove the new lines
        text_body = text_body.replace("\n", " ")

        return final_body, text_body

    @staticmethod
    def get_email_plain_text_body(email):
        body = email.get("payload", {}).get("body", {})

        final_body = base64.urlsafe_b64decode(
            body["data"].encode("utf-8")
        ).decode("utf-8")

        return final_body

    @staticmethod
    def render_email_sender(sender):
        return sender.split("<")[0].strip()

    @staticmethod
    def get_sender(email):
        for header in email.get("payload", {}).get("headers", [{}]):
            if header.get("name", "") == "From":
                return header.get("value", "No Sender")
        return "No Sender"

    @staticmethod
    def get_timestamp(email):
        return datetime.fromtimestamp(int(email.get("internalDate")) / 1000)

    @staticmethod
    def get_snippet(email):
        return email.get("snippet", "No Subject")

    @staticmethod
    def get_email_subject(email):
        for header in email.get("payload", {}).get("headers", [{}]):
            if header.get("name", "") == "Subject":
                return header.get("value", "No Subject")
        return "No Subject"