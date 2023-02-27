import logging

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from src.components.inputs import generate_form_group

logger = logging.Logger(__name__)

dash.register_page(
    __name__, order=3, path_template="/case/<case_id>", exclude=True
)


def layout(case_id):
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
                    dbc.Col("Include a Case Copy", width=4),
                    dbc.Col(
                        dbc.RadioButton(
                            id="lead-media-enabled",
                            persistence_type="session",
                            persistence=True,
                            value=False,
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
                            )
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
    if case_id is None or case_id == "#" or case_id == "none":
        return dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            html.H3(
                                "No Case ID Specified",
                                className="card-title",
                                id="case-id",
                            )
                        )
                    ),
                    width=12,
                ),
            ]
        )
    return [
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            html.H3(
                                [
                                    html.Div(
                                        "Case Details: ", className="mr-1"
                                    ),
                                    html.Div(
                                        case_id,
                                        className="d-none",
                                        id="case-id",
                                    ),
                                ]
                            )
                        )
                    ),
                    width=12,
                    class_name="mb-2",
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            html.H3(
                                                "Lead Status",
                                                className="card-title",
                                            ),
                                            width=4,
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Button(
                                                    "Send SMS",
                                                    color="primary",
                                                    className="mb-2 mr-1",
                                                    id="lead-single-send-sms-button",
                                                ),
                                                dbc.Button(
                                                    "Flag",
                                                    color="primary",
                                                    className="mb-2 ml-2",
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
                    class_name="mb-2",
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
