import logging

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash import html

from src.components.filters import leads_controls
from src.components.inputs import generate_form_group
from src.models import leads as leads_model

logger = logging.Logger(__name__)

dash.register_page(__name__, class_icon="ti ti-file", order=2)


def layout():
    status_options = [
        dbc.Col("Update the leads status", width=3),
        dbc.Col(
            generate_form_group(
                label="Update the leads status",
                id="modal-lead-status",
                placeholder="Set the status",
                type="Dropdown",
                options=[
                    o
                    for o in leads_model.leads_statuses
                    if o["value"] != "all"
                ],
                persistence_type="session",
                persistence=True,
            ),
            width=4,
        ),
    ]
    return html.Div(
        [
            dcc.Store(id="memory", storage_type="memory"),
            html.Div(
                dbc.Modal(
                    [
                        dbc.ModalHeader("More information about selected row"),
                        dbc.ModalBody(id="modal-content"),
                        html.Div(id="hidden-div", style={"display": "none"}),
                        html.Div(id="modal-content-sending-status"),
                        dbc.Row(status_options, className="m-2"),
                        dbc.Row(id="modal-lead-status-update-status"),
                        dbc.Row(
                            id="modal-content-generate-letters-status",
                            className="m-2",
                        ),
                        dbc.ModalFooter(
                            [
                                dbc.Button(
                                    "Update Status",
                                    id="modal-lead-status-update",
                                    className="ml-auto",
                                ),
                                dbc.Button(
                                    "Generate Letters",
                                    id="generate-letters",
                                    className="ml-auto",
                                ),
                                dbc.Button(
                                    "Send all cases",
                                    id="send-all-cases",
                                    className="ml-auto",
                                ),
                                dbc.Button(
                                    "Cancel",
                                    id="send-all-cases-cancel",
                                    className="ml-auto",
                                ),
                            ],
                            className="d-flex justify-content-end",
                        ),
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
