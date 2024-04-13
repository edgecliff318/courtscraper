import base64
import logging

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from flask import session

from src.services.emails import GmailConnector, ParserMessage

logger = logging.Logger(__name__)

dash.register_page(__name__, order=4, path_template="/manage/emails/<email_id>")


def render_file_attachment(attachment):
    filename = attachment[0]
    content = attachment[1]
    b64 = base64.b64encode(content).decode()
    href = f"data:text/plain;base64,{b64}"
    btn = dbc.Button(
        [DashIconify(icon="ph:file-thin", width=20, className="mr-2"), attachment[0]],
        id=f"btn-download-{filename}",
        color="dark",
        className="m-2",
        href=href,
        download=filename,
    )
    return btn


def render_single_email(email):
    user_id = session.get("profile", {}).get("name", None)
    gmail_connector = GmailConnector(user_id=user_id)
    parser = ParserMessage(gmail_connector, email)
    text_parts, attachments = parser.parse_msg(email)
    for part in text_parts:
        if part.get("text/plain"):
            text_body = part.get("text/plain")
        if part.get("text/html"):
            html_body_render = part.get("text/html")

    if len(attachments):
        attachments_content = dmc.Stack(
            [
                dmc.Text(
                    "Attachments",
                    weight=700,
                ),
                dmc.Divider(),
                dmc.Grid(
                    [
                        dmc.Col(
                            render_file_attachment(attachment),
                        )
                        for attachment in attachments
                    ]
                ),
            ]
        )
    else:
        attachments_content = dmc.Stack(
            [
                dmc.Text(
                    "No Attachments",
                    weight=700,
                ),
            ]
        )

    header = dmc.Grid(
        [
            dmc.Col(
                dmc.Text(
                    # Sender
                    gmail_connector.get_sender(email),
                    weight=700,
                ),
                span=3,
            ),
            dmc.Col(
                dmc.Text(
                    # Subject
                    f"{gmail_connector.get_email_subject(email)}",
                    weight=700,
                ),
                span=7,
            ),
            dmc.Col(
                dmc.Text(
                    # Date
                    f"{gmail_connector.get_timestamp(email)}",
                    weight=700,
                ),
                span=2,
            ),
        ],
    )

    return dmc.Stack(
        [
            header,
            dmc.Divider(),
            dash.html.Iframe(
                srcDoc=html_body_render,
                # Iframe should be 100% width and height
                # Iframe should be minimum 100% width and height
                style={
                    "width": "100%",
                    "height": "100%",
                    "min-height": "500px",
                    "min-width": "100%",
                },
            ),
            # Hidden div to store the text body
            dash.html.Div(
                text_body,
                id="email-text-body",
                style={"display": "none"},
            ),
            attachments_content,
            dmc.Divider(),
        ],
    )


def render_reply_section():
    return dmc.Stack(
        [
            dmc.Text(
                "Reply",
                weight=700,
            ),
            dmc.Divider(),
            dmc.Grid(
                [
                    dmc.Col(
                        dmc.Text(
                            "AI Reply",
                        )
                    ),
                    dmc.Col(
                        dmc.Select(
                            data=[
                                {"label": "Prompt#0: Thank you", "value": "1"},
                                {
                                    "label": "Prompt#1: Negative Reply",
                                    "value": "2",
                                },
                                {
                                    "label": "Prompt#2: Neutral Reply",
                                    "value": "3",
                                },
                                {"label": "Template WIP", "value": "3"},
                            ],
                            placeholder="Select a Prompt",
                            id="email-reply-prompt",
                        )
                    ),
                ]
            ),
            dmc.Divider(),
            dmc.Textarea(
                label="Reply",
                placeholder="Enter your reply here...",
                autosize=True,
                minRows=5,
                id="email-reply",
            ),
            dmc.Group(
                [
                    dmc.Button(
                        "Send",
                        variant="filled",
                        color="dark",
                        id="email-reply-button",
                    ),
                    dmc.Button(
                        "Send to All",
                        variant="filled",
                        color="dark",
                        id="email-reply-all-button",
                    ),
                    dmc.Button(
                        "Generate Reply",
                        variant="filled",
                        color="dark",
                        id="email-generate-button",
                    ),
                ]
            ),
        ]
    )


def layout(email_id):
    if email_id is None or email_id == "#" or email_id == "none":
        return dbc.Row(
            [
                dbc.Col(
                    dmc.Paper(
                        shadow="xs",
                        p="md",
                        radius="md",
                        id="emails-list",
                    ),
                    width=12,
                    class_name="mb-2",
                )
            ]
        )

    user_id = session.get("profile", {}).get("name", None)

    if user_id is None:
        # Redirect to login page
        return dash.no_update

    gmail_connector = GmailConnector(user_id=user_id)

    email = gmail_connector.get_email(email_id)

    if email is None:
        return dbc.Row(
            [
                dbc.Col(
                    dmc.Paper(
                        children=[
                            dmc.Alert("Email not found", color="red"),
                        ],
                        shadow="xs",
                        p="md",
                        radius="md",
                    ),
                    width=12,
                ),
                dbc.Col(
                    dmc.Paper(
                        shadow="xs",
                        p="md",
                        radius="md",
                        id="emails-list",
                    ),
                    width=12,
                    class_name="mb-2",
                ),
            ]
        )

    return dbc.Row(
        [
            dbc.Col(
                dmc.Paper(
                    [
                        render_single_email(email),
                        render_reply_section(),
                    ],
                    shadow="xs",
                    p="md",
                    radius="md",
                ),
                width=12,
                class_name="mb-2",
            ),
        ]
    )
