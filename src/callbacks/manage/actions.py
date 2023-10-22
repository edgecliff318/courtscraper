import logging
from datetime import datetime

import dash_mantine_components as dmc
import pytz
from dash import Input, Output, callback, html

from src.components.cases.status import case_statuses, get_case_status_color
from src.core.config import get_settings
from src.services import cases

logger = logging.Logger(__name__)

settings = get_settings()


def convert_date_format(date_str_or_obj, timezone="Etc/GMT-1") -> str:
    if isinstance(date_str_or_obj, datetime):
        date_obj = date_str_or_obj
    else:
        date_obj = datetime.fromisoformat(date_str_or_obj)

    tz = pytz.timezone(timezone)
    date_obj = date_obj.astimezone(tz)

    formatted_date = date_obj.strftime("%B %d, %Y")
    formatted_date = (
        formatted_date[:-2] + ":" + formatted_date[-2:]
    )  # Convert +0100 to +01:00

    return formatted_date


def create_case_card(case_data: dict) -> dmc.Card:
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
                dmc.Text(f"Case: {case_id}", weight=500),
                dmc.Badge(
                    str(status).capitalize(),
                    color=get_case_status_color(status),
                    variant="light",
                ),
            ],
            position="apart",
            mt="md",
            mb="xs",
        ),
        dmc.Text(full_name, weight=500),
        dmc.Text(f"Case Date: {case_date}", size="sm", color="dimmed"),
        dmc.Group(
            [
                dmc.Text(f"Next Action:", size="sm", color="dimmed"),
                dmc.Badge(
                    next_action,
                    color=get_case_status_color(status),
                    variant="light",
                ),
            ],
            mt="md",
            mb="xs",
        ),
        dmc.Text(f"Last Updated: {last_updated}", size="sm", color="dimmed"),
        html.A(
            dmc.Button(
                "View Details",
                variant="light",
                color="blue",
                fullWidth=True,
                mt="md",
                radius="md",
            ),
            href=f"/manage/cases/{case_id}",
        ),
    ]

    return dmc.Card(
        children=card_layout,
        withBorder=True,
        shadow="sm",
        radius="md",
        style={"margin": "6px"},
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


def filter_cases_by_status(cases_list):
    cases_by_status = {"todo": [], "pending": [], "closed": []}

    for case in cases_list:
        case_dic = case.model_dump()
        status = "filed" if not case_dic.get("status") else case_dic["status"]
        section = (
            "todo"
            if not case_statuses[status].get("section")
            else case_statuses[status]["section"]
        )

        if section in cases_by_status:
            cases_by_status[section].append(case_dic)

    return cases_by_status


def create_case_div(cases):
    return html.Div(
        [create_case_card(case) for case in cases], style={"overflowY": "auto"}
    )


@callback(
    Output("case_card_col_1", "children"),
    Output("case_card_col_2", "children"),
    Output("case_card_col_3", "children"),
    Input("court-selector", "value"),
    Input("date-selector", "value"),
)
def render_actions(court_code_list, dates):
    start_date, end_date = dates
    start_date = convert_date_format(start_date)
    end_date = convert_date_format(end_date)

    cases_list = cases.get_cases(court_code_list, None, None, None)
    cases_by_status = filter_cases_by_status(cases_list)

    return (
        create_case_div(cases_by_status["todo"]),
        create_case_div(cases_by_status["pending"]),
        create_case_div(cases_by_status["closed"]),
    )