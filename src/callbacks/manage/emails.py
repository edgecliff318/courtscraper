import logging

import dash
import dash_mantine_components as dmc
import openai
from dash import Input, Output, State, callback, html
from dash_iconify import DashIconify
from flask import session

from src.core.config import get_settings
from src.services.emails import GmailConnector

logger = logging.getLogger(__name__)
settings = get_settings()


@callback(
    Output("emails-list", "children"),
    Input("url", "pathname"),
)
def update_emails_list(pathname):
    user_id = session.get("profile", {}).get("name", None)

    if user_id is None:
        # Redirect to login page
        return dash.no_update

    gmail_connector = GmailConnector(user_id=user_id)

    emails = gmail_connector.get_inbox_emails()

    header = dmc.Grid(
        [
            dmc.Col(
                dmc.Text(
                    "Sender",
                    weight=700,
                ),
                span=3,
            ),
            dmc.Col(
                dmc.Text(
                    "Subject",
                    weight=700,
                ),
                span=6,
            ),
            dmc.Col(
                dmc.Text(
                    "Date",
                    weight=700,
                ),
                span=2,
            ),
        ],
    )

    def render_email_row(email):
        return dmc.Grid(
            [
                dmc.Col(
                    dmc.Text(
                        # Sender
                        f"{gmail_connector.render_email_sender(gmail_connector.get_sender(email))}",
                        weight=700,
                        size="sm",
                    ),
                    span=3,
                ),
                dmc.Col(
                    [
                        dmc.HoverCard(
                            shadow="md",
                            openDelay=1000,
                            width=500,
                            children=[
                                dmc.HoverCardTarget(
                                    dmc.Text(
                                        # Subject
                                        f"{gmail_connector.get_email_subject(email)}",
                                        weight=500,
                                        size="sm",
                                    ),
                                ),
                                dmc.HoverCardDropdown(
                                    dmc.Text(
                                        # Subject
                                        f"{gmail_connector.get_snippet(email)}",
                                        weight=500,
                                        size="sm",
                                    ),
                                    # Return to line
                                    className="p-4 w-96 break-words",
                                ),
                            ],
                        ),
                    ],
                    span=6,
                ),
                dmc.Col(
                    dmc.Text(
                        # Date
                        f"{gmail_connector.get_timestamp(email)}",
                        weight=500,
                        size="sm",
                    ),
                    span=2,
                ),
                dmc.Col(
                    html.A(
                        dmc.ActionIcon(
                            DashIconify(
                                icon="mdi:email",
                            ),
                            color="gray",
                            variant="transparent",
                        ),
                        href=f"/manage/emails/{email['id']}",
                    ),
                    span=1,
                ),
            ],
            id={"type": "email-row", "index": email["id"]},
        )

    emails_renders = [header, dmc.Divider(variant="solid")] + [
        render_email_row(email) for email in emails
    ]

    return dmc.Stack(
        emails_renders,
        spacing="md",
    )


@callback(
    Output("email-reply", "value", allow_duplicate=True),
    Input("email-reply-prompt", "value"),
    prevent_initial_call=True,
)
def update_email_reply(value):
    email_reply_dict = {
        # LLM Prompt to respond positively to the email
        "1": "Write a thank you email to the sender.",
        # LLM Prompt to respond negatively to the email
        "2": "Write a negative email to the sender.",
        # LLM Prompt to respond neutrally to the email
        "3": "Write a neutral email to the sender.",
        # Message to say that we are working on the email in a formal way
        "4": "Hello, \n We are working on your email and will get back to you soon.",
    }

    return email_reply_dict.get(value, "")


@callback(
    Output("email-reply", "value", allow_duplicate=True),
    Input("email-generate-button", "n_clicks"),
    State("email-text-body", "children"),
    State("email-reply", "value"),
    prevent_initial_call=True,
)
def generate_email_reply(n_clicks, email, value):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "email-generate-button":
        openai.api_key = settings.OPENAI_API_KEY

        system_intel = "You are an attorney and you are replying to this email"

        system_intel += "\n\n"

        system_intel += f"The email is {email}"

        prompt = value
        result = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": system_intel},
                {"role": "user", "content": prompt},
            ],
        )

        return result["choices"][0]["message"]["content"]
