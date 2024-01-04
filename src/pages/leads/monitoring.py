import logging

import dash
import dash_bootstrap_components as dbc
from dash import html

from src.components.filters import monitoring_controls

logger = logging.Logger(__name__)

dash.register_page(__name__, class_icon="ti ti-phone", order=3)
import plotly.graph_objects as go

import dash_mantine_components as dmc
from dash import html, Output, Input, callback


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
            # html.Div(id="message-monitoring"),
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
                                            dmc.Button(
                                                "Click Me!", id="graph-skeleton-button"
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
