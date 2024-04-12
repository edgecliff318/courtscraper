import datetime
import logging

import dash_ag_grid as dag
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

from src.core.config import get_settings
from src.core.tools import convert_date_format

logger = logging.getLogger(__name__)
settings = get_settings()


def render_email_row(id, sender, subject, snippet, timestamp):
    return dmc.Grid(
        [
            dmc.Col(
                dmc.Text(
                    sender,
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
                                    snippet,
                                    weight=500,
                                    size="sm",
                                ),
                            ),
                            dmc.HoverCardDropdown(
                                dmc.Text(
                                    subject,
                                    weight=500,
                                    size="sm",
                                ),
                                className="p-4 w-96 break-words",
                            ),
                        ],
                    ),
                ],
                span=6,
            ),
            dmc.Col(
                dmc.Text(
                    convert_date_format(timestamp),
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
                    href=f"/manage/emails/{id}",
                ),
                span=1,
            ),
        ],
        id={"type": "email-row", "index": id},
    )


def render_emails(case):
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

    body = [
        render_email_row(
            email["id"],
            email["sender"],
            email["subject"],
            email["snippet"],
            email["timestamp"],
        )
        for email in case.emails
    ]
    emails_renders = [header, dmc.Divider(variant="solid")] + body

    return dmc.Stack(
        emails_renders,
        spacing="md",
        mt="xl",
    )


def get_case_events(case):
    # Columns : template, document, date, subject, body, email,

    if case.events is None:
        return dmc.Stack(
            children=[
                dmc.Alert(
                    "No events found on this case.",
                    color="gray",
                    variant="filled",
                    sx={"width": "100%"},
                ),
                dmc.Text(
                    "Emails related to this case",
                    weight=700,
                    size="lg",
                ),
                dmc.Divider(variant="solid", size="lg"),
                render_emails(case),
            ],
            spacing="md",
        )

    events = case.events

    for e in events:
        e["date"] = (
            e["date"].strftime("%Y-%m-%d - %H:%M:%S")
            if e["date"] is not None and isinstance(e["date"], datetime.datetime)
            else e["date"]
        )

    return dmc.Stack(
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
            dmc.Text(
                "Emails related to this case",
                weight=700,
                size="lg",
            ),
            dmc.Divider(variant="solid", size="lg"),
            render_emails(case),
        ],
        spacing="md",
    )
