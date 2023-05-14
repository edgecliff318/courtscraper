import logging

import dash
import dash_bootstrap_components as dbc
from dash import html

from src.components.filters import monitoring_controls

logger = logging.Logger(__name__)

dash.register_page(__name__, class_icon="ti chart-bar", order=3)


def layout():
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    monitoring_controls,
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
            html.Div(id="message-monitoring"),
        ]
    )
