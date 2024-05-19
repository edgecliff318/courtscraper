import logging

import dash.html as html
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import Input, Output, callback
from dash_iconify import DashIconify
import dash

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
from src.core.config import get_settings
from src.services import cases

logger = logging.Logger(__name__)

settings = get_settings()


def get_case_tabs(case):
    events_number = len(case.events) if case.events is not None else 0
    tabs = dmc.Tabs(
        [
            dmc.TabsList(
                [
                    dmc.Tab(
                        "Case Workflow",
                        rightSection=DashIconify(icon="tabler:alert-circle", width=16),
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
                        rightSection=DashIconify(icon="et:documents", width=16),
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
            dmc.TabsPanel(get_case_communications(case), value="communications"),
            dmc.TabsPanel(get_case_documents(case), value="documents"),
            dmc.TabsPanel(get_case_payments(case), value="payments"),
            dmc.TabsPanel(get_case_details(case), value="details"),
        ],
        value="workflow",
        persistence=True,
        persistence_type="session",
    )
    return tabs


def case_not_found():
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
                                    # children=case_id,
                                    id="case-id",
                                ),
                                dmc.Button(
                                    "Refresh from Casenet",
                                    color="dark",
                                    id="case-refresh-button",
                                    leftIcon=DashIconify(icon="material-symbols:save"),
                                ),
                                dbc.Col([html.Div(id="case-refresh-button-status")]),
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


def render_case_details(case, title):
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
                dmc.Title(title, order=1, mb="md"),
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
                id="case-manage-summary",
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
                id="case-manage-navigation-components",
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
                id="case-manage-timeline",
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


def get_case_id_from_path(pathname):
    case_id = pathname.split("/")[3] if pathname else None
    if case_id is None or (isinstance(case_id, str) and case_id.lower() == "none"):
        return None
    return case_id


def capitalize_if_not_none(s):
    return s.capitalize() if s is not None else ""


def create_case_title(case):
    first_name = capitalize_if_not_none(case.first_name)
    middle_name = (
        capitalize_if_not_none(case.middle_name[:1]) + "." if case.middle_name else ""
    )
    last_name = capitalize_if_not_none(case.last_name)

    title = (
        f"{first_name} {middle_name}"
        f" {last_name}  - {case.location}"
        f" - {case.case_id}"
    )

    return title


@callback(
    Output("case-manage-summary", "children"),
    Output("case-manage-timeline", "children"),
    [
        #TODO add all the inputs , you want to use in update case info on screen
        
        Input("url", "pathname"),
        Input("url", "search"),
        Input("case-manage-participants", "value"),
        Input("case-upload-to-mycase-button", "n_clicks"),
        Input("case-refresh-button", "n_clicks"),
        Input("case-manage-insert-participants", "n_clicks"),
        Input("case-details-id", "data"),
        Input("case-manage-payments-create-invoice", "n_clicks"),
        Input("case-manage-insert-participants", "n_clicks"),

    ],
    prevent_initial_call=True,
    
)
def render_update_case(pathname, search, *args, **kwargs):
    case_id = get_case_id_from_path(pathname)

    case = cases.get_single_case(case_id)

    return dmc.Paper(
        [
            get_case_summary(case),
        ],
        shadow="xs",
        p="md",
        radius="md",
    ), dmc.Paper(
        [
            get_case_timeline(case),
        ],
        shadow="xs",
        p="md",
        radius="md",
    )


@callback(
    Output("case-manage-details", "children"),
    [Input("url", "pathname"), Input("url", "search")],
)
def update_case(pathname, search):
    case_id = get_case_id_from_path(pathname)

    if case_id is None:
        return case_not_found()
    case = cases.get_single_case(case_id)

    if case is None:
        return case_not_found()

    title = create_case_title(case)

    return render_case_details(case, title)
