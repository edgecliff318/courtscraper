import logging

import dash
import dash_mantine_components as dmc
from dash import html

from src.components.inputs import generate_form_group

logger = logging.Logger(__name__)

dash.register_page(__name__, class_icon="ti ti-file", order=1)


def layout():
    return html.Div(
        [
            generate_form_group(
                label="Courts",
                id="court-selector",
                placeholder="Select a Court",
                type="Dropdown",
                options=[],
                value=None,
                multi=True,
                persistence_type="session",
                persistence=True,
            ),
            html.Div(
                id="leads-queue-refresh",
                style={"display": "none"},
            ),
            dmc.Grid(
                id="leads-queue-grid",
                className="mt-1",
                justify="center",
                align="stretch",
            ),
        ]
    )
