import logging
import sys
from typing import List

import dash
import dash.html as html
import dash_bootstrap_components as dbc
from dash import Input, Output, callback

from src.core.config import get_settings
from src.models import messages as messages_model
from src.services import leads, messages, cases

logger = logging.Logger(__name__)

settings = get_settings()
sys.setrecursionlimit(10000)


def get_table_data(name, details):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3(name, className="card-title"),
                dbc.Table(
                    html.Tbody(
                        [
                            html.Tr(
                                [html.Td(k, style={"font-weight": "700"}), html.Td(v)]
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
    Input("url", "pathname"),
    Input("lead-single-send-sms-button", "n_clicks"),
    Input("lead-single-message", "value"),
    Input("lead-single-been-verified-phone", "value"),
    Input("lead-media-enabled", "value"),
)
def send_message(pathname, sms_button, sms_message, phone, media_enabled):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "lead-single-send-sms-button":
        if "/leads/single" in pathname:
            case_id = pathname.split("/")[-1]
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
                        case_id, sms_message, phone, media_enabled=True
                    )
                except Exception as e:
                    message = f"An error occurred while sending the message. {e}"
                    error = True

            return message


def get_interactions_data(name, interactions: List[messages_model.Interaction]):
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
                                        i.creation_date, style={"font-weight": "700"}
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
    Input("url", "pathname"),
)
def render_case_details(pathname):
    if "/leads/single" in pathname:
        case_id = pathname.split("/")[-1]
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
                                html.H3("An Error Occurred", className="card-title"),
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

            case_details_stored = {"first_name": lead_details.first_name}

            buttons = html.Div(
                [
                    dbc.Button(
                        "Find Manually on BeenVerified",
                        color="primary",
                        href="#",
                        external_link=True,
                        className="mb-2 ml-1",
                        id="lead-single-been-verified-button",
                    )
                ]
            )

            return (
                [
                    dbc.Col(
                        html.H2(
                            f"Case ID: {case_id}, Defendent: {lead_details.first_name}, "
                            f"{lead_details.last_name}, {year_of_birth} ({age})",
                            className="text-left",
                        ),
                        width=8,
                    ),
                    dbc.Col(buttons, width=4),
                    dbc.Col(
                        get_table_data(
                            f"Case {case_id}",
                            case_details.headers,
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        get_table_data(
                            "Charges",
                            case_details.charges,
                        ),
                        width=6,
                    ),
                ],
                "",
                case_details_stored,
            )


@callback(
    Output("lead-single-interactions", "children"),
    Input("url", "pathname"),
    Input("lead-single-message-status", "children"),
)
def render_case_interactions(pathname, status):
    if "/leads/single" in pathname:
        case_id = pathname.split("/")[-1]
        error = False
        try:
            case_id = str(case_id)
        except Exception:
            error = True

        if not error:
            interactions = messages.get_interactions(case_id)
            output = get_interactions_data("Interactions", interactions)
            return output
