import logging

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify

from src.components.inputs import generate_form_group
from src.models.cases import Case
from src.services import cases

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


case_statuses = {
    "filed": {
        "value": "filed",
        "label": "Case Filed on casenet",
        "color": "gray",
    },
    "paid": {
        "value": "paid",
        "label": "Client Paid",
        "color": "green",
    },
    "eoa": {
        "value": "eoa",
        "label": "Entry of Appearance",
        "color": "indigo",
    },
    "rev_int": {
        "value": "rev_int",
        "label": "Internal Review",
        "color": "yellow",
    },
    "def_dev": {
        "value": "def_dev",
        "label": "Review with the client",
        "color": "yellow",
    },
    "rec_rfr": {
        "value": "rec_rfr",
        "label": "RFR Filing",
        "color": "orange",
    },
    "rec_rec": {
        "value": "rec_rec",
        "label": "Recommendation Received",
        "color": "lime",
    },
    "rec_rej": {
        "value": "rec_rej",
        "label": "Recommendation Rejected",
        "color": "red",
    },
    "rec_del": {
        "value": "rec_del",
        "label": "Recommendation Delayed",
        "color": "pink",
    },
    "rec_rev": {
        "value": "rec_rev",
        "label": "Recommendation Review",
        "color": "yellow",
    },
    "rec_prop": {
        "value": "rec_prop",
        "label": "Recommendation Proposed to Client",
        "color": "green",
    },
    "rec_sig": {
        "value": "rec_sig",
        "label": "Recommendation pending signature",
        "color": "orange",
    },
    "rec_sub": {
        "value": "rec_sub",
        "label": "Recommendation to submit to court",
        "color": "orange",
    },
    "rec_sub_rev": {
        "value": "rec_sub_rev",
        "label": "Recommendation Submission under Review by the Court",
        "color": "orange",
    },
    "app": {
        "value": "app",
        "label": "Court Appearance Required",
        "color": "red",
    },
    "close": {
        "value": "close",
        "label": "Close Case on Portal",
        "color": "lime",
    },
}


def get_case_status_color(status: str | None):
    if status is None:
        return "gray"
    return case_statuses[status]["color"]


def create_group_item(label: str, value: str | None, icon: str):
    return dmc.Group(
        [
            dmc.Group(
                [
                    DashIconify(icon=icon),
                    dmc.Text(
                        label,
                        weight=500,
                    ),
                ],
                spacing="sm",
            ),
            dmc.Text(
                value if value is not None else "N/A",
                size="sm",
                color="dimmed",
            ),
        ],
        position="apart",
    )


"""
{
  id:string
  case_desc: string
  case_id: string
  case_type: string
  charges: Charge[]
  court_desc: string
  criminal_case: boolean
  disposed: boolean
  dockets: Docket[]
  parties: Party[]
  filing_date: Timestamp
  first_name: string
  last_name: string
  formatted_telephone: string
  judge: Judge
  plea_andpayind: string
  status: string
  fine: string
  paid: boolean
}
"""


def get_case_details(case: Case):
    charges = []
    if case.charges is not None:
        charges = [
            dmc.Text(
                charge.get("charge_description", ""),
                size="sm",
            )
            for charge in case.charges
        ]

    return dmc.Paper(
        [
            dmc.Group(
                [
                    dmc.Text(f"Case#{case.case_id}", weight=500),
                    dmc.Badge(
                        case.status.capitalize()
                        if case.status is not None
                        else "Filed",
                        color=get_case_status_color(case.status),
                        variant="light",
                    ),
                ],
                position="apart",
                mt="md",
                mb="xs",
            ),
            dmc.Divider(variant="solid", className="mt-2"),
            dmc.Title("→ Case Details", order=5, className="mt-1"),
            create_group_item(
                label="Filing Date",
                value=f"{case.filing_date:%B %d, %Y}",
                icon="radix-icons:calendar",
            ),
            # Court Description
            create_group_item(
                label="Court",
                value=case.court_desc,
                icon="mdi:gavel",
            ),
            create_group_item(
                label="Fine",
                value=f"$ {case.fine.get('total_amount', 'N/A') if case.fine is not None else 'N/A'}",
                icon="mdi:cash",
            ),
            dmc.Divider(variant="solid", className="mt-2"),
            dmc.Title("→ Charges", order=5, className="mt-1"),
            html.Div(charges),
            dmc.Divider(variant="solid", className="mt-2"),
            dmc.Title("Defendant", order=5, className="mt-1"),
            create_group_item(
                label="Name",
                value=case.formatted_party_name,
                icon="material-symbols:supervised-user-circle-outline",
            ),
            create_group_item(
                label="Date of Birth",
                value=f"{case.birth_date}",
                icon="ps:birthday",
            ),
            create_group_item(
                label="Address",
                value="",
                icon="material-symbols:location-on-outline",
                # Left align
            ),
            dmc.Text(
                case.formatted_party_address,
                size="sm",
                color="dimmed",
                # Right align
                style={"text-align": "right"},
            ),
            create_group_item(
                label="Phone",
                value=case.formatted_telephone,
                icon="material-symbols:phone-android-outline",
            ),
            dmc.Divider(variant="solid", className="mt-2"),
            dmc.Title("→ Judge", order=5, className="mt-1"),
            create_group_item(
                label="Name",
                value=case.judge.get("formatted_name", "")
                if case.judge is not None
                else "",
                icon="fluent-emoji-high-contrast:man-judge",
            ),
            dmc.Divider(variant="solid", className="mt-2"),
            dmc.Title("→ Parties", order=5, className="mt-1"),
            html.Div(
                [
                    html.Div(
                        [
                            dmc.Title(party.get("desc", ""), order=6),
                            create_group_item(
                                label="Name",
                                value=party.get("formatted_partyname", ""),
                                icon="material-symbols:supervised-user-circle-outline",
                            ),
                            create_group_item(
                                label="Phone",
                                value=party.get("formatted_telephone", ""),
                                icon="material-symbols:phone-android-outline",
                            ),
                            create_group_item(
                                label="Address",
                                value="",
                                icon="material-symbols:location-on-outline",
                            ),
                            dmc.Text(
                                party.get("formatted_partyaddress", ""),
                                size="sm",
                                color="dimmed",
                                # Right align
                                style={"text-align": "right"},
                            ),
                        ]
                    )
                    for party in case.parties
                ]
            )
            if case.parties is not None
            else "",
        ]
    )


def get_case_search():
    case_select = dmc.Select(
        label="Select a Case",
        style={"width": "100%"},
        icon=DashIconify(icon="radix-icons:magnifying-glass"),
        rightSection=DashIconify(icon="radix-icons:chevron-down"),
        searchable=True,
        id="case-select",
    )
    return [
        html.Div(
            id="case-search",
        ),
        html.Div(
            id="case-select",
            children=case_select,
            className="m-1",
        ),
    ]


def layout(case_id):
    if case_id is None or case_id == "#" or case_id == "none":
        return dbc.Row(
            [
                dbc.Col(
                    dmc.Paper(
                        get_case_search(),
                        shadow="xs",
                        p="md",
                        radius="md",
                    ),
                    width=12,
                    class_name="mb-2",
                )
            ]
        )

    case = cases.get_single_case(case_id)

    if case is None:
        return dbc.Row(
            [
                dbc.Col(
                    dmc.Paper(
                        get_case_search(),
                        shadow="xs",
                        p="md",
                        radius="md",
                    ),
                    width=12,
                    class_name="mb-2",
                ),
                dbc.Col(
                    dmc.Paper(
                        children=[
                            dmc.Alert("Case not found", color="red"),
                        ],
                        shadow="xs",
                        p="md",
                        radius="md",
                    ),
                    width=12,
                ),
            ]
        )

    return dbc.Row(
        [
            dbc.Col(
                dmc.Paper(
                    get_case_search(),
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
                        get_case_details(case),
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
                        get_case_timeline(case),
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
