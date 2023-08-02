import logging

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify

from src.components.inputs import generate_form_group
from src.models.cases import Case

logger = logging.Logger(__name__)

dash.register_page(__name__, order=3, path_template="/manage/<case_id>")


def get_court_section():
    stack = dmc.Stack(
        children=[
            dmc.Select(
                data=[
                    "Entry of Appearance",
                    "Motion to Continue",
                    "Motion to Withdraw",
                ],
                value="Entry of Appearance",
                label="Document Template",
                icon=DashIconify(icon="radix-icons:magnifying-glass"),
                rightSection=DashIconify(icon="radix-icons:chevron-down"),
            ),
            dmc.Button(
                "Preview",
                leftIcon=DashIconify(icon="fluent:preview-link-20-filled"),
            ),
            dmc.Button(
                "Submit to Court",
                leftIcon=DashIconify(
                    icon="fluent:database-plug-connected-20-filled"
                ),
            ),
        ],
        style={"maxWidth": "400px"},
    )

    return stack


def get_prosecutor_section():
    stack = dmc.Stack(
        children=[
            dmc.Select(
                data=[
                    "RFR Template#1 - Chat GPT",
                    "RFR Template#2 - Chat GPT",
                    "RFR Template#3 - Fixed",
                ],
                value="RFR Template#1 - Chat GPT",
                label="Email Template",
                icon=DashIconify(icon="radix-icons:magnifying-glass"),
                rightSection=DashIconify(icon="radix-icons:chevron-down"),
            ),
            dmc.Button(
                "Preview",
                leftIcon=DashIconify(icon="fluent:preview-link-20-filled"),
            ),
            dmc.Button(
                "Submit to Prosecutor",
                leftIcon=DashIconify(
                    icon="fluent:database-plug-connected-20-filled"
                ),
            ),
        ],
        style={"maxWidth": "400px"},
    )
    return stack


def get_client_section():
    stack = dmc.Stack(
        children=[
            dmc.Select(
                data=[
                    "RFR Reply#1 - Chat GPT",
                    "RFR Reply#2 - Chat GPT",
                    "RFR Reply#3 - Template",
                ],
                value="RFR Reply#1 - Chat GPT",
                label="Document Template",
                icon=DashIconify(icon="radix-icons:magnifying-glass"),
                rightSection=DashIconify(icon="radix-icons:chevron-down"),
            ),
            dmc.Button(
                "Preview",
                leftIcon=DashIconify(icon="fluent:preview-link-20-filled"),
            ),
            dmc.Button(
                "Submit to Client by Email & SMS",
                leftIcon=DashIconify(
                    icon="fluent:database-plug-connected-20-filled"
                ),
            ),
        ],
        style={"maxWidth": "400px"},
    )

    return stack


def get_case_workflow():
    return dmc.Accordion(
        children=[
            dmc.AccordionItem(
                [
                    dmc.AccordionControl(
                        "Work with the Court",
                        icon=DashIconify(
                            icon="tabler:gavel",
                            color=dmc.theme.DEFAULT_COLORS["blue"][6],
                            width=20,
                        ),
                    ),
                    dmc.AccordionPanel(get_court_section()),
                ],
                value="court",
            ),
            dmc.AccordionItem(
                [
                    dmc.AccordionControl(
                        "Work with the Prosecutor",
                        icon=DashIconify(
                            icon="tabler:analyze",
                            color=dmc.theme.DEFAULT_COLORS["blue"][6],
                            width=20,
                        ),
                    ),
                    dmc.AccordionPanel(
                        get_prosecutor_section(),
                    ),
                ],
                value="prosecutor",
            ),
            dmc.AccordionItem(
                [
                    dmc.AccordionControl(
                        "Work with the Client",
                        icon=DashIconify(
                            icon="tabler:user",
                            color=dmc.theme.DEFAULT_COLORS["blue"][6],
                            width=20,
                        ),
                    ),
                    dmc.AccordionPanel(
                        get_client_section(),
                    ),
                ],
                value="client",
            ),
        ],
    )


def get_case_messages():
    return


def get_case_settings():
    return


def get_case_tabs():
    tabs = dmc.Tabs(
        [
            dmc.TabsList(
                [
                    dmc.Tab(
                        "Case Workflow",
                        rightSection=DashIconify(
                            icon="tabler:alert-circle", width=16
                        ),
                        value="workflow",
                    ),
                    dmc.Tab(
                        "Messages",
                        rightSection=dmc.Badge(
                            "6",
                            size="xs",
                            p=0,
                            variant="filled",
                            sx={
                                "width": 16,
                                "height": 16,
                                "pointerEvents": "none",
                            },
                        ),
                        value="messages",
                    ),
                    dmc.Tab(
                        "Settings",
                        rightSection=DashIconify(
                            icon="tabler:alert-circle", width=16
                        ),
                        value="settings",
                    ),
                ]
            ),
            dmc.TabsPanel(get_case_workflow(), value="workflow"),
            dmc.TabsPanel(get_case_messages(), value="messages"),
            dmc.TabsPanel(get_case_settings(), value="settings"),
        ],
        value="workflow",
    )
    return tabs


def get_case_timeline(case: Case):
    timeline = dmc.Timeline(
        active=1,
        bulletSize=15,
        lineWidth=2,
        children=[
            dmc.TimelineItem(
                title="Case Created & Paid",
            ),
            dmc.TimelineItem(
                title="EOA",
                children=[
                    dmc.Text(
                        [
                            "EOA submitted by ",
                            dmc.Anchor("Shawn Meyer", href="#", size="sm"),
                            " on ",
                            dmc.Anchor("2021-01-01", href="#", size="sm"),
                        ],
                        color="dimmed",
                        size="sm",
                    ),
                ],
            ),
            dmc.TimelineItem(
                title="RFR Pending",
                lineVariant="dashed",
                children=[
                    dmc.Text(
                        [
                            "RFR submitted by ",
                            dmc.Anchor(
                                "Shawn Meyer",
                                href="#",
                                size="sm",
                            ),
                            " on ",
                            dmc.Anchor("2021-01-01", href="#", size="sm"),
                        ],
                        color="dimmed",
                        size="sm",
                    ),
                ],
            ),
            dmc.TimelineItem(
                title="RFR Approved",
                children=[
                    dmc.Text(
                        ["RFR to be approved by the client &  the attorney"],
                    )
                ],
            ),
            dmc.TimelineItem(
                title="RFR Signed",
                children=[
                    dmc.Text(
                        [
                            "RFR to be signed by the client",
                        ]
                    )
                ],
            ),
            dmc.TimelineItem(
                title="RFR Paid by Client",
                children=[
                    dmc.Text(
                        [
                            "RFR Agreement paid by the client",
                        ]
                    )
                ],
            ),
            dmc.TimelineItem(
                title="Court Acceptance",
                children=[
                    dmc.Text(
                        [
                            "Court to accept the RFR proposal",
                        ]
                    )
                ],
            ),
            dmc.TimelineItem(
                title="Case Closed",
                children=[
                    dmc.Text(
                        [
                            "Case closed and archived",
                        ]
                    )
                ],
            ),
        ],
    )
    return timeline


def get_case_details(case: Case):
    return dmc.Paper(
        [
            dmc.Group(
                [
                    dmc.Text("Case#2222", weight=500),
                    dmc.Badge("Paid", color="red", variant="light"),
                ],
                position="apart",
                mt="md",
                mb="xs",
            ),
            dmc.Text(
                "High speed",
                size="sm",
                color="dimmed",
            ),
        ]
    )


def layout(case_id):
    messaging_module = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col("Sample Messages", width=4),
                    dbc.Col(
                        generate_form_group(
                            label="Sample Message",
                            id="lead-single-message-selector",
                            placeholder="Select a Sample Message",
                            type="Dropdown",
                            options=[],
                            persistence_type="session",
                            persistence=True,
                        ),
                        width=8,
                    ),
                ],
                className="mb-1",
            ),
            dbc.Row(
                [
                    dbc.Col("Include a Case Copy", width=4),
                    dbc.Col(
                        dbc.RadioButton(
                            id="lead-media-enabled",
                            persistence_type="session",
                            persistence=True,
                            value=False,
                        ),
                        width=8,
                    ),
                ],
                className="mb-1",
            ),
            dbc.Row(
                [
                    dbc.Col("Phone Number", width=4),
                    dbc.Col(
                        [
                            generate_form_group(
                                label="Phone Number",
                                id="lead-single-phone",
                                placeholder="Set the phone number",
                                type="Input",
                            )
                        ],
                        width=8,
                    ),
                ],
                className="mb-1",
            ),
            dbc.Row(
                [
                    dbc.Col("Email", width=4),
                    dbc.Col(
                        [
                            generate_form_group(
                                label="Email",
                                id="lead-single-email",
                                placeholder="Set the email",
                                type="Input",
                            )
                        ],
                        width=8,
                    ),
                ],
                className="mb-1",
            ),
            dbc.Row(
                [
                    dbc.Col("Message", width=4),
                    dbc.Col(
                        generate_form_group(
                            label="Message",
                            id="lead-single-message",
                            placeholder="Type in the message",
                            type="Textarea",
                            style={"height": 300},
                        ),
                        width=8,
                    ),
                ]
            ),
            dbc.Row([dbc.Col(id="lead-single-message-status")]),
        ]
    )
    if case_id is None or case_id == "#" or case_id == "none":
        case_select = dmc.Select(
            label="Select a Case",
            style={"width": "100%"},
            icon=DashIconify(icon="radix-icons:magnifying-glass"),
            rightSection=DashIconify(icon="radix-icons:chevron-down"),
            searchable=True,
            id="case-select",
        )
        return dbc.Row(
            [
                dbc.Col(
                    dmc.Paper(
                        [
                            html.Div(
                                id="case-search",
                            ),
                            html.Div(
                                id="case-select",
                                children=case_select,
                                className="m-1",
                            ),
                        ],
                        shadow="xs",
                        p="md",
                        radius="md",
                    ),
                    width=12,
                    class_name="mb-2",
                ),
                dbc.Col(
                    dmc.Paper(
                        [
                            get_case_details(None),
                        ],
                        shadow="xs",
                        p="md",
                        radius="md",
                    ),
                    width=3,
                    class_name="mb-2",
                ),
                dbc.Col(
                    dmc.Paper(
                        [get_case_tabs()],
                        shadow="xs",
                        p="md",
                        radius="md",
                    ),
                    width=6,
                    class_name="mb-2",
                ),
                dbc.Col(
                    dmc.Paper(
                        [
                            get_case_timeline(None),
                        ],
                        shadow="xs",
                        p="md",
                        radius="md",
                    ),
                    width=3,
                    class_name="mb-2",
                ),
            ]
        )

    return [
        dbc.Row(
            dbc.Col(
                dmc.Paper(
                    children=[],
                    shadow="xs",
                    p="md",
                    radius="md",
                ),
                width=2,
            )
        )
    ]
