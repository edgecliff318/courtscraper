import logging

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, html

from src.components.conversation import many_response_model
from src.components.filters import monitoring_controls

logger = logging.Logger(__name__)

dash.register_page(__name__, class_icon="ti ti-phone", order=3)


def layout():
    skeleton_cards = dmc.Grid(
        children=[
            dmc.GridCol(
                dmc.Skeleton(
                    height="150px",
                    width="23vw",
                ),
                span={"base": 12, "md": 3},
            )
            for i in range(4)
        ],
        style={"overflow": "hidden"},
    )

    skeleton_card = html.Div(
        dmc.Skeleton(
            height="400px",
            width="90vw",
        ),
        style={"overflow": "hidden"},
    )

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
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            children=skeleton_cards, id="messages-summary"
                        ),
                        width=12,
                        className="mb-2 p-1",
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(
                                        children=skeleton_card,
                                        id="message-monitoring",
                                    )
                                ]
                            )
                        ),
                        width=12,
                        className="mb-2 p-1",
                    ),
                ]
            ),
            html.Div(
                id="leads-data",
            ),
            html.Div(
                [
                    many_response_model("monitoring"),
                    dcc.Store(id="monitoring-data", storage_type="memory"),
                    many_response_model("conversation"),
                    dcc.Store(id="conversation-data", storage_type="memory"),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(
                                        children=skeleton_card,
                                        id="graph-container-status-sms",
                                    )
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2 p-1",
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
                                        children=skeleton_card,
                                        id="graph-container-most-recent-error",
                                    )
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2 p-1",
                    ),
                ]
            ),
        ]
    )
