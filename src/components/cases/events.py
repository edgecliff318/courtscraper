import datetime
import logging
import os

import dash
import dash_ag_grid as dag
import dash_mantine_components as dmc
import openai
from dash import ALL, Input, Output, State, callback, html
from dash_iconify import DashIconify
from flask import session
import pandas as pd

from src.core.config import get_settings
from src.services.emails import GmailConnector

logger = logging.getLogger(__name__)
settings = get_settings()


import re

def extract_number_from_string(s):
    match = re.search(r'\b\d+\b', s)
    if match:
        return match.group(0)
    return None


def render_email_row(id,sender, subject, timestamp):
    
 
    return dmc.Grid(
            [
                dmc.Col(
                    dmc.Text(
                        f"{sender}",
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
                                        f"{subject}",
                                        weight=500,
                                        size="sm",
                                    ),
                                ),
                                dmc.HoverCardDropdown(
                                    dmc.Text(
                                        # Subject
                                        f"{subject}",
                                        weight=500,
                                        size="sm",
                                    ),
                                    # Return to line
                                    className="p-4 w-96 break-words",
                                ),
                            ],
                        ),
                    ],
                    span=7,
                ),
                dmc.Col(
                    dmc.Text(
                        # Date
                        f"{timestamp}",
                        weight=500,
                        size="sm",
                    ),
                    span=2,
                ),
            ],
            id={"type": "email-row", "index": id},
        )

def update_emails_list(case_id=None):
    user_id = session.get("profile", {}).get("name", None)

    if user_id is None:
        # Redirect to login page
        return dash.no_update

    gmail_connector = GmailConnector(user_id=user_id)

    emails = gmail_connector.get_inbox_emails()
    emails_list = []

    for email in emails:
        case_number = extract_number_from_string(gmail_connector.get_email_subject(email))

        emails_list+=[{
            "id": email["id"],
            "case_number": case_number,
            "subject": gmail_connector.get_email_subject(email),
            "sender": gmail_connector.render_email_sender(gmail_connector.get_sender(email)),
            "timestamp": gmail_connector.get_timestamp(email).strftime("%Y-%m-%d")
        }]
        
    emails_df = pd.DataFrame(emails_list)
    emails_df = emails_df.sort_values(by="timestamp", ascending=False)
    emails_df = emails_df[["case_number"] == "231020430"]
    

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
                span=3,
            ),
        ],
    )

    body = [render_email_row(email["id"], email["sender"], email["subject"], email["timestamp"]) for _, email in emails_df.iterrows()]
    emails_renders = [header, dmc.Divider(variant="solid")] + body 
   

    return dmc.Stack(
        emails_renders,
        spacing="md",
        mt="lg",
    )
    

def get_case_events(case):
    # Columns : template, document, date, subject, body, email,

    if case.events is None:
        return html.Div(
            children=[
                dmc.Alert(
                    "No events found on this case.",
                    color="gray",
                    variant="filled",
                    sx={"width": "100%"},
                ),
                update_emails_list()
                ,
            ]
        )

    events = case.events

    for e in events:
        e["date"] = (
            e["date"].strftime("%Y-%m-%d - %H:%M:%S")
            if e["date"] is not None and isinstance(e["date"], datetime.datetime)
            else e["date"]
        )

    return html.Div(
        children=[
            dag.AgGrid(
                id="case-events",
                columnDefs=[
                    {
                        "headerName": "Template",
                        "field": "template",
                        "filter": "agTextColumnFilter",
                        "sortable": True,
                        "resizable": True,
                        "flex": 1,
                    },
                    {
                        "headerName": "Date",
                        "field": "date",
                        "editable": True,
                        "filter": "agDateColumnFilter",
                        "sortable": True,
                        "resizable": True,
                        "flex": 1,
                    },
                ],
                rowData=events,
                dashGridOptions={
                    "undoRedoCellEditing": True,
                    "rowSelection": "multiple",
                    "rowMultiSelectWithClick": True,
                },
            ),
            update_emails_list()
            ,
        ]
    )
