import logging

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

from src.components.cases.communications import get_case_communications
from src.components.cases.details import get_case_details
from src.components.cases.documents import get_case_documents
from src.components.cases.events import get_case_events
from src.components.cases.next_steps import get_next_step_modal
from src.components.cases.payments import get_case_payments
from src.components.cases.search import get_case_search
from src.components.cases.summary import get_case_summary
from src.components.cases.timeline import get_case_timeline
from src.components.cases.workflow.workflow import get_case_workflow
from src.services import cases

logger = logging.Logger(__name__)

dash.register_page(__name__, order=3, path_template="/manage/cases/<case_id>")


def get_case_tabs(case):
    events_number = len(case.events) if case.events is not None else 0
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
                        "Events",
                        rightSection=dmc.Badge(
                            events_number,
                            size="xs",
                            p=0,
                            variant="filled",
                            sx={
                                "width": 16,
                                "height": 16,
                                "pointerEvents": "none",
                            },
                        ),
                        value="events",
                    ),
                    dmc.Tab(
                        "Communications",
                        rightSection=DashIconify(
                            icon="material-symbols:comment-outline", width=16
                        ),
                        value="communications",
                    ),
                    dmc.Tab(
                        "Documents",
                        rightSection=DashIconify(
                            icon="et:documents", width=16
                        ),
                        value="documents",
                    ),
                    dmc.Tab(
                        "Payments",
                        rightSection=DashIconify(
                            icon="fluent:payment-32-regular", width=16
                        ),
                        value="payments",
                    ),
                    dmc.Tab(
                        "Details",
                        rightSection=DashIconify(
                            icon="carbon:folder-details", width=16
                        ),
                        value="details",
                    ),
                ]
            ),
            dmc.TabsPanel(get_case_workflow(case), value="workflow"),
            dmc.TabsPanel(get_case_events(case), value="events"),
            dmc.TabsPanel(
                get_case_communications(case), value="communications"
            ),
            dmc.TabsPanel(get_case_documents(case), value="documents"),
            dmc.TabsPanel(get_case_payments(case), value="payments"),
            dmc.TabsPanel(get_case_details(case), value="details"),
        ],
        value="workflow",
        persistence=True,
        persistence_type="session",
    )
    return tabs


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
                            dmc.Alert(
                                [
                                    dmc.Text("Case not found", mb="xs"),
                                    html.Div(
                                        hidden=True,
                                        children=case_id,
                                        id="case-id",
                                    ),
                                    dmc.Button(
                                        "Refresh from Casenet",
                                        color="dark",
                                        id="case-refresh-button",
                                        leftIcon=DashIconify(
                                            icon="material-symbols:save"
                                        ),
                                    ),
                                    dbc.Col(
                                        [
                                            html.Div(
                                                id="case-refresh-button-status"
                                            )
                                        ]
                                    ),
                                ],
                                color="red",
                            )
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
                        get_case_summary(case),
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
                    [get_case_tabs(case), get_next_step_modal()],
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
            dbc.Col(
                [
                    html.Div(id="case-refresh-button-status"),
                    html.Div(id="case-upload-to-mycase-button-status"),
                ]
            ),
        ]
    )
