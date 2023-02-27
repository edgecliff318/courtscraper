import logging

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html


from src.components.inputs import generate_form_group

logger = logging.Logger(__name__)

dash.register_page(__name__, class_icon="ti ti-file", order=3)


def layout():
    messaging_module = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col("Sample Messages", width=4),
                    dbc.Col(
                        generate_form_group(
                            label="Sample Message",
                            id="lead-single-message-selector",
                            placeholder="Select a Sample Message",
                            type="Dropdown",
                            options=[],
                            persistence_type="session",
                            persistence=True,
                        ),
                        width=8,
                    ),
                ],
                className="mb-1",
            ),
            dbc.Row(
                [
                    dbc.Col("Phone Number", width=4),
                    dbc.Col(
                        [
                            generate_form_group(
                                label="Phone Number",
                                id="lead-single-been-verified-phone",
                                placeholder="Set the phone number",
                                type="Input",
                                persistence_type="session",
                                persistence=True,
                            ),
                            dbc.FormGroup(
                                [
                                    dbc.Checkbox(
                                        id="lead-single-been-verified-media",
                                        className="form-check-input",
                                    ),
                                    dbc.Label(
                                        "Media Enabled",
                                        html_for="lead-single-been-verified-media",
                                        className="form-check-label",
                                    ),
                                ],
                            ),
                        ],
                        width=8,
                    ),
                ],
                className="mb-1",
            ),
            dbc.Row(
                [
                    dbc.Col("Message", width=4),
                    dbc.Col(
                        generate_form_group(
                            label="Message",
                            id="lead-single-message",
                            placeholder="Type in the message",
                            type="Textarea",
                            style={"height": 300},
                        ),
                        width=8,
                    ),
                ]
            ),
            dbc.Row([dbc.Col(id="lead-single-message-status")]),
        ]
    )
    return [
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            html.H3(
                                                "Lead Status", className="card-title"
                                            ),
                                            width=4,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Button(
                                                    "Send SMS",
                                                    color="primary",
                                                    className="mb-2 ml-1",
                                                    id="lead-single-send-sms-button",
                                                ),
                                                dbc.Button(
                                                    "Flag",
                                                    color="primary",
                                                    className="mb-2 ml-1",
                                                    id="lead-single-flag",
                                                ),
                                            ],
                                            width=8,
                                        ),
                                    ]
                                ),
                                html.Div(messaging_module),
                            ]
                        ),
                    ),
                    width=6,
                ),
                dbc.Col(id="lead-single-been-verified", width=6),
                dbc.Col(id="lead-single-interactions", width=12),
            ]
        ),
        dbc.Row(id="lead-single"),
        html.Div(id="lead-single-been-verified-trigger"),
        dcc.Store(id="lead-single-case-details"),
    ]
