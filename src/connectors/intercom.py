"""
Connector to Intercom to send messages to the contacts
"""
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class IntercomConnector:
    def __init__(self, api_key) -> None:
        self.api_key = api_key
        self.base_url = "https://api.intercom.io"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Intercom-Version": "2.9",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_contact(self, contact_id):
        contact = self.session.get(f"{self.base_url}/contacts/{contact_id}")
        return contact.json()

    def search_contact(
        self, email=None, phone=None, name=None
    ) -> Optional[dict]:
        query = None

        if email is not None:
            query = {
                "query": {"field": "email", "operator": "=", "value": email}
            }

        if phone is not None:
            query = {
                "query": {"field": "phone", "operator": "=", "value": phone}
            }

        if name is not None:
            query = {
                "query": {
                    "field": "name",
                    "operator": "=",
                    "value": name,
                }
            }

        contact = self.session.post(
            f"{self.base_url}/contacts/search", json=query
        )

        if contact.status_code == 404:
            logger.error(f"Contact not found: {contact}")
            return None

        contact = contact.json()

        if contact.get("type") == "error.list":
            logger.error(f"An error happened : {contact}")
            raise Exception("An error happened with Intercom API")

        if contact.get("type") == "list":
            contacts_list = contact.get("data")
            if len(contacts_list) == 1:
                return contacts_list[0]

            if len(contacts_list) > 1:
                logger.error(f"More than one contact found: {contact}")
                raise Exception("More than one contact found")

            return None

        return contact.get("data")

    def get_admins(self):
        admins = self.session.get(f"{self.base_url}/admins")
        return admins.json().get("admins")

    def get_admin(self, admin_id):
        admin = self.session.get(f"{self.base_url}/admins/{admin_id}")
        return admin.json()

    def send_message(self, sender, contact, message):
        url = f"{self.base_url}/messages"

        payload = {
            "message_type": "email",
            "subject": "Hey there!",
            "template": "personal",
            "from": {"type": sender.get("type"), "id": sender.get("id")},
            "body": message,
            "to": {"type": contact.get("type"), "id": contact.get("id")},
        }

        response = self.session.post(url, json=payload)

        data = response.json()
        return data

    def get_conversation(self, conversation_id):
        url = f"{self.base_url}/conversations/{conversation_id}"
        response = self.session.get(url)
        return response.json()

    def get_conversations_by_contact(self, contact):
        url = f"{self.base_url}/conversations/search"
        payload = {
            "query": {
                "field": "contact_ids",
                "operator": "=",
                "value": contact.get("id"),
            }
        }
        response = self.session.post(url, json=payload)
        return response.json()


if __name__ == "__main__":
    from src.core.config import get_settings

    settings = get_settings()

    intercom = IntercomConnector(settings.INTERCOM_API_KEY)

    contact = intercom.search_contact(email="shawn@tickettakedown.com")
    admins = intercom.get_admins()

    message = """
<!doctype html><html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office"><head><title></title><!--[if !mso]><!--><meta http-equiv="X-UA-Compatible" content="IE=edge"><!--<![endif]--><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style type="text/css">#outlook a { padding:0; }
          body { margin:0;padding:0;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%; }
          table, td { border-collapse:collapse;mso-table-lspace:0pt;mso-table-rspace:0pt; }
          img { border:0;height:auto;line-height:100%; outline:none;text-decoration:none;-ms-interpolation-mode:bicubic; }
          p { display:block;margin:13px 0; }</style><!--[if mso]>
        <noscript>
        <xml>
        <o:OfficeDocumentSettings>
          <o:AllowPNG/>
          <o:PixelsPerInch>96</o:PixelsPerInch>
        </o:OfficeDocumentSettings>
        </xml>
        </noscript>
        <![endif]--><!--[if lte mso 11]>
        <style type="text/css">
          .mj-outlook-group-fix { width:100% !important; }
        </style>
        <![endif]--><!--[if !mso]><!--><link href="https://fonts.googleapis.com/css?family=Open Sans" rel="stylesheet" type="text/css"><style type="text/css">@import url(https://fonts.googleapis.com/css?family=Open Sans);</style><!--<![endif]--><style type="text/css">@media only screen and (min-width:480px) {
        .mj-column-per-100 { width:100% !important; max-width: 100%; }
      }</style><style media="screen and (min-width:480px)">.moz-text-html .mj-column-per-100 { width:100% !important; max-width: 100%; }</style><style type="text/css">[owa] .mj-column-per-100 { width:100% !important; max-width: 100%; }</style><style type="text/css">@media only screen and (max-width:480px) {
      table.mj-full-width-mobile { width: 100% !important; }
      td.mj-full-width-mobile { width: auto !important; }
    }</style></head><body style="word-spacing:normal;background-color:#f8f8f8;"><div style="background-color:#f8f8f8;"><!--[if mso | IE]><table align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600" bgcolor="#ffffff" ><tr><td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;"><![endif]--><div style="background:#ffffff;background-color:#ffffff;margin:0px auto;max-width:600px;"><table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#ffffff;background-color:#ffffff;width:100%;"><tbody><tr><td style="direction:ltr;font-size:0px;padding:20px 0;padding-bottom:0px;padding-top:0px;text-align:center;"><!--[if mso | IE]><table role="presentation" border="0" cellpadding="0" cellspacing="0"><tr><td class="" style="vertical-align:top;width:600px;" ><![endif]--><div class="mj-column-per-100 mj-outlook-group-fix" style="font-size:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%"><tbody><tr><td align="center" style="font-size:0px;padding:10px 25px;padding-top:40px;padding-right:50px;padding-bottom:0px;padding-left:50px;word-break:break-word;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" style="border-collapse:collapse;border-spacing:0px;"><tbody><tr><td style="width:300px;"><img alt="" height="auto" src="https://www.mailjet.com/wp-content/uploads/2019/07/Welcome-02.png" style="border:none;display:block;outline:none;text-decoration:none;height:auto;width:100%;font-size:13px;" width="300"></td></tr></tbody></table></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><![endif]--></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><table align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600" bgcolor="#ffffff" ><tr><td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;"><![endif]--><div style="background:#ffffff;background-color:#ffffff;margin:0px auto;max-width:600px;"><table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#ffffff;background-color:#ffffff;width:100%;"><tbody><tr><td style="direction:ltr;font-size:0px;padding:20px 0px 20px 0px;padding-bottom:70px;padding-top:30px;text-align:center;"><!--[if mso | IE]><table role="presentation" border="0" cellpadding="0" cellspacing="0"><tr><td class="" style="vertical-align:top;width:600px;" ><![endif]--><div class="mj-column-per-100 mj-outlook-group-fix" style="font-size:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%"><tbody><tr><td align="left" style="font-size:0px;padding:0px 25px 0px 25px;padding-top:0px;padding-right:50px;padding-bottom:0px;padding-left:50px;word-break:break-word;"><div style="font-family:Open Sans, Helvetica, Arial, sans-serif;font-size:13px;line-height:22px;text-align:left;color:#797e82;"><h1 style="text-align:center; color: #000000; line-height:32px">Welcome Shawn ! We are so happy to have you on board.</h1></div></td></tr><tr><td align="left" style="font-size:0px;padding:0px 25px 0px 25px;padding-top:0px;padding-right:50px;padding-bottom:0px;padding-left:50px;word-break:break-word;"><div style="font-family:Open Sans, Helvetica, Arial, sans-serif;font-size:13px;line-height:22px;text-align:left;color:#797e82;"><p style="margin: 10px 0; text-align: center;">We are taking care of your ticket.</p></div></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><![endif]--></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><![endif]--></div></body></html>
    """
    message = intercom.send_message(
        sender=admins[0], contact=contact, message=message
    )

    conversation = intercom.get_conversations_by_contact(contact=contact)

    print(conversation)

    pass
