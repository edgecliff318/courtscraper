import logging

import dash_mantine_components as dmc

from dash import Input, Output, callback, html

from src.components.cases.status import case_statuses, get_case_status_color
from src.core.config import get_settings
from src.core.tools import convert_date_format
from src.core.dynamic_fields import CaseDynamicFields
from src.services import cases

logger = logging.Logger(__name__)

settings = get_settings()


def create_case_card(case_data: dict):
    location_name = (
        f"{case_data.get('location')} Court of {case_data.get('city')}"
    )
    date_str_or_obj_time = case_data.get("court_time", "")
    date_str_or_obj = case_data.get("court_date", "")
    case_date = "No Court Date"
    if date_str_or_obj:
        date_obj = datetime.strptime(date_str_or_obj, "%m/%d/%Y")
        case_date = (
            f"{convert_date_format(date_obj)} at {date_str_or_obj_time}"
        )
        # Red if in less than 7 days from now
        # Orange if in less than 30 days from now
        # Green if in more than 30 days from now
        court_date_color = "green"

        if (date_obj - datetime.now()).days < 7:
            court_date_color = "red"
        elif (date_obj - datetime.now()).days < 30:
            court_date_color = "orange"
    else:
        court_date_color = "red"

    charges_description = case_data.get("charges_description", "")
    case_id = case_data.get("case_id", "N/A")
    status = case_data.get("status") or "filed"
    full_name = (
        f'{case_data.get("first_name", "")} {case_data.get("last_name", "")}'
    )

    card_layout = [
        dmc.Group(
            [
                dmc.Text(f"Case#{case_id}", weight=500),
                dmc.Badge(
                    case_statuses.get(status, {}).get(
                        "short_description", status
                    ),
                    color=get_case_status_color(status),
                    variant="light",
                ),
            ],
            position="apart",
            spacing="xs",
        ),
        dmc.Text(
            f"{full_name.lower().capitalize()}",
            size="sm",
            color="dark",
        ),
        dmc.Group(
            [
                dmc.Text(
                    f"{case_date.lower().capitalize()}",
                    size="sm",
                    color=court_date_color,
                ),
                dmc.Text(
                    f"{location_name.lower().capitalize()}",
                    size="sm",
                    color="dimmed",
                ),
            ],
            position="apart",
            spacing="xs",
        ),
        dmc.Text(
            f"{charges_description.lower().capitalize()}",
            size="sm",
            color="dark",
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

def parse_date_time(case):
    date_str = case.get("court_date", "01/01/1900") or "01/01/1900"
    time_str = case.get("court_time", "12:00 AM") or "12:00 AM"
    sort_date_str = f"{date_str} {time_str}"
    try:
        return datetime.strptime(sort_date_str, "%m/%d/%Y %I:%M %p")
    except ValueError:
        return datetime.strptime("01/01/1900 12:00 AM", "%m/%d/%Y %I:%M %p")


def create_case_div(cases):
    updated_cases = []

    for case in cases:
        case = CaseDynamicFields().update(case, case.model_dump())
        case["sort_date"] = parse_date_time(case)
        updated_cases.append(case)

    df = pd.DataFrame(updated_cases)
    if df.empty:
        return html.Div(style={"overflowY": "auto"})
    df["sort_date"] = pd.to_datetime(df["sort_date"])
    df = df.sort_values("sort_date", ascending=True)
    updated_cases = df.to_dict("records")

    case_cards = [create_case_card(case) for case in updated_cases]

    return html.Div(case_cards, style={"overflowY": "auto"})


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
