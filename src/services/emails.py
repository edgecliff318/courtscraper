import base64
import html.parser
import logging
import mimetypes
from datetime import datetime
from email.message import EmailMessage
from time import sleep
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
from googleapiclient.discovery import build

from src.services.emails_auth import get_credentials

# Number of seconds the subscriber should listen for messages
TIMEOUT = 200000

logger = logging.getLogger(__name__)


"""

example of usage
    email_id = "18ed4465cf0e6886"
    user_id = "ayoub@tickettakedown.com"
    
    connector = GmailConnector(user_id)
    msg = connector.get_email(email_id)

    parser = ParserMessage(connector, msg)
    text_parts, attachments = parser.parse_msg(msg)
    print(text_parts)
    print(attachments)

"""


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


class ParserMessage:
    def __init__(self, connector, msg: dict) -> None:
        self.msg = msg
        self.connector = connector

    def decode_base64(self, data: str) -> bytes:
        return base64.urlsafe_b64decode(data.encode("ASCII"))

    def fetch_attachment(
        self, part: dict, message_id: str
    ) -> Optional[Tuple[str, bytes]]:
        filename = part.get("filename", "")
        attachment_id = part.get("body", {}).get("attachmentId")
        if not attachment_id:
            return None

        result = (
            self.connector.service.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=message_id, id=attachment_id)
            .execute()
        )
        data = result["data"]
        file_data = base64.urlsafe_b64decode(data.encode("ASCII"))
        logger.info(f"Attachment {filename} fetched")

        return filename, file_data

    def get_text_part(
        self, parts: List[Dict[str, Any]], message_id: str
    ) -> Tuple[List[dict[str, str]], List[Tuple[str, bytes]]]:
        text_parts = []
        attachments = []

        for part in parts:
            content_type = part.get("mimeType", "")
            body_data = part.get("body", {}).get("data", "")
            filename = part.get("filename", "")

            if "parts" in part:
                sub_parts = part["parts"]
                sub_text_parts, sub_attachments = self.get_text_part(
                    sub_parts, message_id
                )
                text_parts.extend(sub_text_parts)
                attachments.extend(sub_attachments)

            if filename:
                filename, body_data = self.fetch_attachment(part, message_id)
                attachments.append((filename, body_data))

            if (
                content_type == "text/plain" or content_type == "text/html"
            ) and body_data:
                content = self.decode_base64(body_data).decode("utf-8")
                text_parts.append({content_type: content})

        return text_parts, attachments

    def parse_msg(
        self, msg: Dict[str, Any]
    ) -> Tuple[List[dict[str, str]], List[Tuple[str, bytes]]]:
        if "parts" in msg["payload"]:
            return self.get_text_part(msg["payload"]["parts"], msg["id"])
        else:
            content_type = msg["payload"].get("mimeType", "")
            body_data = msg["payload"].get("body", {}).get("data", "")
            if content_type == "text/plain" and body_data:
                return [
                    {content_type: self.decode_base64(body_data).decode("utf-8")}
                ], []
            elif content_type == "text/html" and body_data:
                return [
                    {content_type: self.decode_base64(body_data).decode("utf-8")}
                ], []
            else:
                return [], []


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

    def get_inbox_emails(self, total_results=None):
        if total_results is None:
            # Get all the emails in the inbox
            total_results = (
                self.service.users()
                .getProfile(userId="me")
                .execute()
                .get("messagesTotal")
            )
        messages = []
        total = 0
        next_page_token = None
        while True:
            try:
                emails = (
                    self.service.users()
                    .messages()
                    .list(userId="me", maxResults=20, pageToken=next_page_token)
                    .execute()
                )

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
                total += len(emails.get("messages", []))
                sleep(0.5)
                print(f"Got the first {total} emails")
                next_page_token = emails.get("nextPageToken")
                if total >= total_results:
                    break
            except Exception as error:
                print("An error occurred: %s" % error)
                raise error

        return [
            {
                "id": message["id"],
                "snippet": message["snippet"],
                "payload": message["payload"],
                "internalDate": message["internalDate"],
            }
            for message in messages
        ]

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
                header["value"] for header in headers if header["name"] == "Subject"
            ][0]

            return {
                "subject": subject,
                "sender": [
                    header["value"] for header in headers if header["name"] == "From"
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
                .get(userId="me", id=email_id, format="full")
                .execute()
            )
            return email

        except Exception as error:
            logger.error(f"An error occurred while retrieving {email_id}: {error}")

    def text_to_html(self, text):
        return text.replace("\n", "<br>")

    def send_email(self, subject, message, to, attachments=None):
        try:
            logger.info(f"Sending email with subject {subject} to {to}")
            # Use the HTML MIME type

            mime_message = EmailMessage()

            # headers
            mime_message["To"] = to
            mime_message["From"] = "me"
            mime_message["Subject"] = subject

            # Replace
            message = self.text_to_html(message)

            # text
            mime_message.set_content(
                message,
                subtype="html",
            )

            # attachment
            if attachments is None:
                attachments = []

            for attachment_filename in attachments:
                # guessing the MIME type
                type_subtype, _ = mimetypes.guess_type(attachment_filename)
                maintype, subtype = type_subtype.split("/")

                filename = attachment_filename.name

                with open(attachment_filename, "rb") as fp:
                    attachment_data = fp.read()
                mime_message.add_attachment(
                    attachment_data, maintype, subtype, filename=filename
                )

            encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

            create_message = {"raw": encoded_message}
            send_message = (
                self.service.users()
                .messages()
                .send(userId="me", body=create_message)
                .execute()
            )
            return send_message

        except Exception as error:
            logger.error(f"An error occurred: {error}")
            raise error

    @staticmethod
    def get_email_html_body(email):
        body = email.get("payload", {}).get("body", {})

        if body.get("data") is None:
            multipart = email.get("payload", {}).get("parts", [])

            for part in multipart:
                if part.get("mimeType") == "text/html":
                    body = part.get("body", {})
                    break

        final_body = base64.urlsafe_b64decode(
            body.get("data", "").encode("utf-8")
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

        final_body = base64.urlsafe_b64decode(body["data"].encode("utf-8")).decode(
            "utf-8"
        )

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
