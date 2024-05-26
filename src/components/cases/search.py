import logging

import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

logger = logging.Logger(__name__)


def get_case_search():
    case_select = dmc.Select(
        label="Select a Case",
        style={"width": "100%"},
        leftSection=DashIconify(icon="radix-icons:magnifying-glass"),
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
