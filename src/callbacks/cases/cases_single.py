import logging
from typing import List

import dash
import dash.html as html
import dash_bootstrap_components as dbc
from dash import Input, Output, callback

from src.core.config import get_settings
from src.models import messages as messages_model
from src.services import cases, leads, messages

logger = logging.Logger(__name__)

settings = get_settings()


def get_table_data(name, details):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3(name, className="card-title"),
                dbc.Table(
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Td(k, style={"font-weight": "700"}),
                                    html.Td(v),
                                ]
                            )
                            for k, v in details.items()
                        ]
                    ),
                    hover=True,
                    responsive=True,
                ),
            ]
        ),
        className="mb-2",
    )


@callback(
    Output("lead-single-message-status", "children"),
    Input("case-id", "children"),
    Input("lead-single-send-sms-button", "n_clicks"),
    Input("lead-single-message", "value"),
    Input("lead-single-been-verified-phone", "value"),
    Input("lead-media-enabled", "value"),
)
def send_message(case_id, sms_button, sms_message, phone, media_enabled):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "lead-single-send-sms-button":
        if case_id is None:
            return "No case ID found"
        error = False
        message = ""
        try:
            case_id = str(case_id)
        except Exception:
            message = "Case ID must be a number"
            error = True

        if not error:
            try:
                message = messages.send_message(
                    case_id, sms_message, phone, media_enabled=media_enabled
                )
            except Exception as e:
                message = f"An error occurred while sending the message. {e}"
                error = True

        return message


def get_interactions_data(
    name, interactions: List[messages_model.Interaction]
):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3(name, className="card-title"),
                dbc.Table(
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Td(
                                        i.creation_date,
                                        style={"font-weight": "700"},
                                    ),
                                    html.Td(i.message),
                                    html.Td(i.type),
                                    html.Td(i.status),
                                ]
                            )
                            for i in interactions
                        ]
                    ),
                    hover=True,
                    responsive=True,
                ),
            ]
        ),
        className="mb-2",
    )


@callback(
    Output("lead-single", "children"),
    Output("lead-single-been-verified-trigger", "children"),
    Output("lead-single-case-details", "data"),
    Output("lead-single-been-verified-phone", "value"),
    Input("case-id", "children"),
)
def render_case_details(case_id):
    if case_id is None:
        return (
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3(
                                    "An Error Occurred", className="card-title"
                                ),
                                html.P("No case ID found"),
                            ]
                        ),
                    ),
                    width=12,
                    className="mb-2",
                )
            ],
            None,
            None,
        )

    error = False
    message = ""
    try:
        case_id = str(case_id)
    except Exception:
        message = "Case ID must be a number"
        error = True

    if error:
        return [
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H3(
                                "An Error Occurred", className="card-title"
                            ),
                            html.P(message),
                        ]
                    ),
                ),
                width=12,
                className="mb-2",
            )
        ]

    else:
        case_details = cases.get_single_case(case_id)
        lead_details = leads.get_single_lead(case_id)
        year_of_birth = lead_details.year_of_birth
        age = lead_details.age

        charges = case_details.charges

        return (
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            html.H4(
                                f"Case ID: {case_id}, "
                                f"Defendant: {lead_details.first_name}, "
                                f"{lead_details.last_name}, {year_of_birth} ({age})",
                                className="text-left",
                            )
                        ),
                        class_name="mb-2",
                    ),
                    width=12,
                ),
                dbc.Col(
                    get_table_data(
                        f"Case {case_id}",
                        case_details.headers,
                    ),
                    width=6,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("Charges", className="card-title"),
                                html.P(charges),
                            ]
                        ),
                        className="mb-2",
                    ),
                    width=6,
                ),
            ],
            "",
            lead_details.dict(),
            lead_details.phone,
        )


@callback(
    Output("lead-single-interactions", "children"),
    Input("case-id", "children"),
    Input("lead-single-message-status", "children"),
)
def render_case_interactions(case_id, status):
    if case_id is None:
        return dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H3("An Error Occurred", className="card-title"),
                        html.P("No case ID found"),
                    ]
                ),
            ),
            width=12,
            className="mb-2",
        )
    error = False
    try:
        case_id = str(case_id)
    except Exception:
        error = True

    if not error:
        interactions = messages.get_interactions(case_id)
        output = get_interactions_data("Interactions", interactions)
        return output
