import logging

import dash
import dash_bootstrap_components as dbc
from dash import html

from src.components.filters import leads_controls

logger = logging.Logger(__name__)

dash.register_page(__name__, class_icon="ti ti-file", order=2)


def layout():
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    leads_controls,
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
            dbc.Row([], id="cases-data"),
            dbc.Row([], id="leads-data"),
        ]
    )
