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


def create_case_card(case_details: dict):
    from datetime import datetime
    from src.core.dynamic_fields import CaseDynamicFields
    from src.models import cases

    case_data = CaseDynamicFields().update(cases.Case(**case_details), case_details)
    location_name = f"{case_data.get('location')} Court of {case_data.get('city')}"
    date_str_or_obj_time = case_data.get("court_time", "")
    date_str_or_obj = case_data.get("court_date", "")
    if date_str_or_obj:
        date_obj = datetime.strptime(date_str_or_obj, "%m/%d/%Y")
        case_date = f"{convert_date_format(date_obj)} at {date_str_or_obj_time}"
    else:
        case_date = "not available"

    charges_description = case_data.get("charges_description", "")

    case_id = case_data.get("case_id", "N/A")
    status = (
        "filed"
        if case_data.get("status") == "" or case_data.get("status") is None
        else case_data.get("status")
    )

    full_name = f'{case_data.get("first_name", "")} {case_data.get("last_name", "")}'


    card_layout = [
        dmc.Group(
            [
                dmc.Text(f"Case#{case_id}", weight=500),
                # dmc.Text(full_name, weight=500),
                dmc.Badge(
                    case_statuses.get(status, {}).get("short_description", status),
                    color=get_case_status_color(status),
                    variant="light",
                ),
            ],
            position="apart",
        ),
                dmc.Text(f"User name: {full_name.lower().capitalize()}", size="sm", color="dimmed"),
                dmc.Text(f"Court Date: {case_date.lower().capitalize()}", size="sm", color="dimmed"),
                dmc.Text(f"Court Location: {location_name.lower().capitalize()}", size="sm", color="dimmed"),
                dmc.Text(f"charges : {charges_description.lower().capitalize()}", size="sm", color="dimmed"),
            
       
       
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
                html.H4(title, style={"marginTop": "4px", "textAlign": "center"}),
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
