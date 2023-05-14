import logging
from datetime import timedelta
from typing import List

import dash
import dash.html as html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback

from src.core.config import get_settings
from src.db import bucket
from src.models import messages as messages_model
from src.services import cases, leads, messages

logger = logging.Logger(__name__)

settings = get_settings()


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

        charges = lead_details.charges_description

        parties = pd.DataFrame(case_details.parties)
        columns = [
            "desc",
            "formatted_partyname",
            "formatted_telephone",
            "formatted_partyaddress",
        ]
        parties = parties[columns].rename(
            columns={
                "desc": "Party Type",
                "formatted_partyname": "Name",
                "formatted_telephone": "Phone",
                "formatted_partyaddress": "Address",
            }
        )
        column_defs = [
            {"field": c, "sortable": True, "filter": True}
            for c in parties.columns
        ]
        parties_ag_grid = dag.AgGrid(
            id="portfolio-grid",
            columnDefs=column_defs,
            rowData=parties.to_dict("records"),
            # Fit to content
            columnSize="autoSize",
            style={"height": 200},
        )

        # Documents
        documents = pd.DataFrame(case_details.documents)
        columns = ["docket_desc", "file_path", "document_extension"]
        documents = documents[columns].rename(
            columns={
                "docket_desc": "Description",
                "file_path": "File Path",
                "document_extension": "Extension",
            }
        )
        # Generate the link from Firebase bucket
        documents["File Path"] = documents["File Path"].apply(
            lambda x: (
                f"[Download]"
                f"({bucket.get_blob(x).generate_signed_url(expiration=timedelta(seconds=3600))})"
            )
        )

        column_defs = [
            {
                "field": "Description",
                "sortable": True,
                "filter": True,
                "flex": 1,
            },
            {
                "field": "File Path",
                "sortable": True,
                "filter": True,
                "flex": 1,
                "sortable": True,
                "resizable": True,
                "cellRenderer": "markdown",
            },
            {
                "field": "Extension",
                "sortable": True,
                "filter": True,
                "flex": 1,
            },
        ]
        documents_ag_grid = dag.AgGrid(
            id="portfolio-grid",
            columnDefs=column_defs,
            rowData=documents.to_dict("records"),
            # Fit to content
            columnSize="autoSize",
            style={"height": 200},
        )

        filing_date = case_details.filing_date
        if filing_date is not None:
            filing_date = filing_date.strftime("%m/%d/%Y")

        case_details_info = dbc.Table(
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td("Case ID", className="font-weight-bold"),
                            html.Td(case_id),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td(
                                "Filing Date", className="font-weight-bold"
                            ),
                            html.Td(filing_date),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td("Case Type", className="font-weight-bold"),
                            html.Td(case_details.case_type),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td(
                                "Case Status", className="font-weight-bold"
                            ),
                            html.Td(lead_details.status),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td("Charges", className="font-weight-bold"),
                            html.Td(charges),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td(
                                "Date of Birth", className="font-weight-bold"
                            ),
                            html.Td(year_of_birth),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td("Age", className="font-weight-bold"),
                            html.Td(age),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td("Phone", className="font-weight-bold"),
                            html.Td(lead_details.phone),
                        ]
                    ),
                ]
            ),
            hover=True,
            responsive=True,
            striped=True,
            bordered=True,
        )

        return (
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3(
                                    "Case Details", className="card-title"
                                ),
                                case_details_info,
                            ]
                        ),
                        class_name="mb-2",
                    ),
                    width=6,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("Documents", className="card-title"),
                                documents_ag_grid,
                            ]
                        ),
                        className="mb-2",
                    ),
                    width=6,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("Parties", className="card-title"),
                                parties_ag_grid,
                            ]
                        ),
                        className="mb-2",
                    ),
                    width=12,
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
