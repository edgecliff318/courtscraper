import os
import dash_bootstrap_components as dbc
import logging

from dash import html

import components
from components.figures import empty_figure
from components.inputs import generate_form_group

logger = logging.Logger(__name__)


def page():
    controls = html.Div([
        dbc.Row(
            [
                dbc.Col(html.H3("Courts", className="align-middle"),
                        width=1),
                dbc.Col(
                    components.inputs.generate_form_group(
                        label="Measure",
                        id="court-selector",
                        placeholder="Select a Court",
                        type="Dropdown", options=[],
                        value="0",
                        multi=True,
                        persistence_type="session",
                        persistence=True
                    ),
                    width=7
                ),
                dbc.Col(
                    components.inputs.generate_form_group(
                        label="Date",
                        id="date-selector",
                        placeholder="Select a Date",
                        type="DatePickerSingle",
                        persistence_type="session",
                        persistence=True
                    ),
                    width=2
                ),
                dbc.Col(
                    dbc.Button("Search", id="search-button"),
                    width=1
                ),
                dbc.Col(
                    dbc.Button("Leads", id="leads-button"),
                    width=1
                )
            ]
        )
    ])
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    controls,
                                ]
                            ),
                        ),
                        width=12
                    ),

                ]
            ),
            dbc.Row(
                [],
                id="cases-data"
            ),
            dbc.Row(
                [],
                id="leads-data"
            )
        ]
    )


def single():
    messagine_module = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        "Sample Messages",
                        width=4
                    ),
                    dbc.Col(
                        generate_form_group(
                            label="Sample Message",
                            id="lead-single-message-selector",
                            placeholder="Select a Sample Message",
                            type="Dropdown", options=[],
                            persistence_type="session",
                            persistence=True
                        ),
                        width=8

                    )
                ], className="mb-1",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        "Message",
                        width=4
                    ),
                    dbc.Col(
                        generate_form_group(
                            label="Message", id="lead-single-message",
                            placeholder="Type in the message",
                            type="Textarea"
                        ),
                        width=8
                    )
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        id="lead-single-message-status"
                    )
                ]
            )
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
                                            html.H3("Lead Status",
                                                    className="card-title"),
                                            width=4
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Button(
                                                    "Send SMS",
                                                    color="primary",
                                                    className="mb-2 ml-1",
                                                    id="lead-single-send-sms-button"
                                                ),
                                                dbc.Button(
                                                    "Flag", color="primary",
                                                    className="mb-2 ml-1",
                                                    id="lead-single-flag"
                                                )
                                            ],
                                            width=8
                                        )
                                    ]
                                ),
                                html.Div(messagine_module),
                            ]
                        ),
                    ),
                    width=6
                ),
                dbc.Col(
                    id="lead-single-been-verified",
                    width=6
                ),
                dbc.Col(
                    id="lead-single-interactions",
                    width=12
                )
            ]
        ),
        dbc.Row(
            id="lead-single"
        ),
        html.Div(id="lead-single-been-verified-trigger"),
    ]
