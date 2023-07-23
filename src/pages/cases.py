import logging

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from src.components.inputs import generate_form_group
from src.models import leads as leads_model

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
                                id="lead-single-phone",
                                placeholder="Set the phone number",
                                type="Input",
                            )
                        ],
                        width=8,
                    ),
                ],
                className="mb-1",
            ),
            dbc.Row(
                [
                    dbc.Col("Email", width=4),
                    dbc.Col(
                        [
                            generate_form_group(
                                label="Email",
                                id="lead-single-email",
                                placeholder="Set the email",
                                type="Input",
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

    # Lead status and internal notes
    lead_admin_module = html.Div(
        [
            dbc.Row(
                html.Div(id="lead-single-letter-status"),
            ),
            dbc.Row(
                [
                    dbc.Col("Status", width=4),
                    dbc.Col(
                        generate_form_group(
                            label="Status",
                            id="lead-single-status",
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
                        width=8,
                    ),
                ],
                className="mb-1",
            ),
            dbc.Row(
                [
                    dbc.Col("Internal Notes", width=4),
                    dbc.Col(
                        generate_form_group(
                            label="Internal Notes",
                            id="lead-single-notes",
                            placeholder="Type in internal notes",
                            type="Textarea",
                            style={"height": 370},
                        ),
                        width=8,
                    ),
                ]
            ),
            dbc.Row([dbc.Col(id="lead-single-admin-status")]),
        ]
    )
    lead_admin_card = dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Lead",
                                className="card-title",
                            ),
                            width=4,
                        ),
                        dbc.Col(
                            [
                                html.Div(id="lead-single-save-status"),
                            ],
                            width=2,
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    id="case-upload-to-mycase-button-status"
                                ),
                            ],
                            width=2,
                        ),
                        dbc.Col(
                            [
                                html.Div(id="case-refresh-button-status"),
                            ],
                            width=2,
                        ),
                    ]
                ),
                html.Div(lead_admin_module),
            ]
        ),
    )

    # Top menu actions
    case_actions = [
        dbc.Button(
            "Upload to MyCase",
            color="primary",
            className="m-1 p-2",
            id="case-upload-to-mycase-button",
        ),
        dbc.Button(
            "Letter",
            color="dark",
            className="p-2 m-1",
            id="lead-generate-pdf-button",
        ),
        dbc.Button(
            "Refresh",
            color="primary",
            className="m-1 p-2",
            id="case-refresh-button",
        ),
        dbc.Button(
            "Save",
            color="primary",
            className="m-1 p-2",
            id="lead-single-save-button",
        ),
    ]

    return [
        dbc.Row(
            [
                html.Div(
                    case_id,
                    className="d-none",
                    id="case-id",
                ),
                dbc.Col(
                    case_actions,
                    width=12,
                    class_name="mb-2 d-flex justify-content-end",
                ),
            ],
        ),
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
                                                "Messaging",
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
                                                )
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
                    lg=6,
                    xs=12,
                ),
                dbc.Col(lead_admin_card, lg=6, xs=12, class_name="mb-2"),
                dbc.Col(id="lead-single-been-verified", lg=12, xs=12),
                dbc.Col(id="lead-single-interactions", width=12),
            ]
        ),
        dbc.Row(id="lead-single"),
        html.Div(id="lead-single-been-verified-trigger"),
        dcc.Store(id="lead-single-case-details"),
    ]
