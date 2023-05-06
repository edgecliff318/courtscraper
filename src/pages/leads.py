import logging

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash import html

from src.components.filters import leads_controls

logger = logging.Logger(__name__)

dash.register_page(__name__, class_icon="ti ti-file", order=2)


def layout():
    return html.Div(
        [   
            dcc.Store(id='memory', storage_type = 'memory'),

            html.Div(
                 dbc.Modal(
            [
                dbc.ModalHeader("More information about selected row"),
                dbc.ModalBody(id="modal-content"),
                html.Div(id="modal-content-sending-status"),
                dbc.ModalFooter(dbc.Button("Send all cases", id="send-all-cases", className="ml-auto")),
            ],
            id="modal",
            size="xl",


        ),
            className="m-3",
                 ),
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
            dbc.Row([html.Div(id="selections-multiple-click-output")]),
        ]
    )
