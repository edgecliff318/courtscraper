import logging

import dash
import dash_bootstrap_components as dbc
from dash import html
import dash_mantine_components as dmc

from src.components.filters import monitoring_controls

logger = logging.Logger(__name__)

dash.register_page(__name__, class_icon="ti ti-phone", order=3)


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
                                    html.Div(id="monitoring-status"),
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
            html.Div(id="message-monitoring"),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            dmc.Skeleton(
                                                visible=False,
                                                children=html.Div(
                                                    id="graph-container-status-sms",
                                                ),
                                                mb=10,
                                            ),
                                        ]
                                    )
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
            # most recent error
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            dmc.Skeleton(
                                                visible=False,
                                                children=html.Div(
                                                    id="graph-container-most-recent-error",
                                                ),
                                                mb=10,
                                            ),
                                        ]
                                    )
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
        ]
    )
