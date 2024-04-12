import logging

import dash_mantine_components as dmc
from dash import Input, Output, callback, html

from src.components.cases.status import case_statuses, get_case_status_color
from src.core.config import get_settings
from src.core.tools import convert_date_format
from src.services import cases

logger = logging.Logger(__name__)

settings = get_settings()



def create_case_card(case_data: dict):
    case_id = case_data.get("case_id", "N/A")
    status = (
        "filed"
        if case_data.get("status") == "" or case_data.get("status") is None
        else case_data.get("status")
    )
    priority = case_data.get("priority", False)

    first_name = case_data.get("first_name", "")
    last_name = case_data.get("last_name", "")
    full_name = f"{first_name} {last_name}"

    case_date = convert_date_format(case_data.get("case_date", ""))
    next_action = case_data.get("next_action", "N/A")
    next_action = (
        "filed"
        if case_data.get("status") == "" or case_data.get("status") is None
        else case_data.get("status")
    )

    last_updated = convert_date_format(
        case_data.get("last_updated", case_data.get("case_date", ""))
    )

    card_layout = [
        dmc.Group(
            [
                dmc.Text(f"Case#{case_id}", weight=500),
                dmc.Text(full_name, weight=500),
            ],
            position="apart",
        ),
        dmc.Group(
            [
                dmc.Text("Status"),
                dmc.Badge(
                    case_statuses.get(status, {}).get(
                        "short_description", status
                    ),
                    color=get_case_status_color(status),
                    variant="light",
                ),
            ],
            position="apart",
        ),
        dmc.Text(f"Case Date: {case_date}", size="sm", color="dimmed"),
        dmc.Text(f"Last Updated: {last_updated}", size="sm", color="dimmed"),
        dmc.Text("Suggested Action"),
        dmc.Group(
            [
                dmc.Badge(
                    next_action,
                    color=get_case_status_color(status),
                    variant="light",
                ),
            ]
        ),
        dmc.Group(
            [
                html.A(
                    dmc.Button(
                        "Suggested Action",
                        variant="light",
                        color="dark",
                        fullWidth=True,
                        mt="md",
                        radius="md",
                    ),
                    href=f"/manage/cases/{case_id}",
                ),
                html.A(
                    dmc.Button(
                        "Send Reminder",
                        variant="light",
                        color="dark",
                        fullWidth=True,
                        mt="md",
                        radius="md",
                    ),
                    href=f"/manage/cases/{case_id}",
                ),
            ]
        ),
    ]

    return html.A(
        children=dmc.Card(
            children=card_layout,
            withBorder=True,
            shadow="sm",
            radius="md",
            style={"margin": "6px"},
        ),
        href=f"/manage/cases/{case_id}",
    )


def create_case_column(cases, title):
    """Generate a column of case cards with a title."""
    return dmc.Col(
        dmc.Navbar(
            p="md",
            children=[
                html.H4(
                    title, style={"marginTop": "4px", "textAlign": "center"}
                ),
                dmc.Divider(size="sm", style={"marginBottom": "10px"}),
                html.Div(
                    [create_case_card(case) for case in cases],
                    style={"overflowY": "auto"},
                ),
            ],
        ),
        xl=4,
        lg=4,
        md=12,
        sm=12,
        xs=12,
    )


def create_case_div(cases):
    return html.Div(
        [create_case_card(case.model_dump()) for case in cases],
        style={"overflowY": "auto"},
    )


@callback(
    Output("case_card_col_todo", "children"),
    Input("court-selector", "value"),
)
def render_actions_todo(court_code_list):
    cases_list_todo = cases.get_cases(court_code_list, flag="todo")
    return create_case_div(cases_list_todo)


@callback(
    Output("case_card_col_pending", "children"),
    Input("court-selector", "value"),
)
def render_actions_pending(court_code_list):
    cases_list_pending = cases.get_cases(court_code_list, flag="pending")
    return create_case_div(cases_list_pending)


@callback(
    Output("case_card_col_closed", "children"),
    Input("court-selector", "value"),
)
def render_actions_closed(court_code_list):
    cases_list_closed = cases.get_cases(court_code_list, flag="closed")
    return create_case_div(cases_list_closed)
