import logging
from datetime import timedelta
from typing import List

import dash
import dash.html as html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, State, callback

from src.components.toast import build_toast
from src.core.config import get_settings
from src.core.format import humanize_phone
from src.db import bucket
from src.loader.leads import CaseNet
from src.models import cases as cases_model
from src.models import messages as messages_model
from src.services import cases, leads, letters, messages
from src.services.settings import get_account

logger = logging.Logger(__name__)

settings = get_settings()


@callback(
    Output("lead-single-message-status", "children"),
    Input("case-id", "children"),
    Input("lead-single-send-sms-button", "n_clicks"),
    Input("lead-single-message", "value"),
    Input("lead-single-phone", "value"),
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
            message = build_toast(message, "Error", "danger")

        toast = None
        if not error:
            try:
                message = messages.send_message(
                    case_id, sms_message, phone, media_enabled=media_enabled
                )
                toast = build_toast(
                    f"Message sent succesfully {message}",
                    "Message Sent",
                    "success",
                )
            except Exception as e:
                message = f"An error occurred while sending the message. {e}"
                error = True
                toast = build_toast(message, "Error", "danger")

        return toast


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
    Output("lead-single-been-verified", "children"),
    Output("lead-single-case-details", "data"),
    Output("lead-single-phone", "value"),
    Output("lead-single-email", "value"),
    Output("lead-single-status", "value"),
    Output("lead-single-notes", "value"),
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
            None,
            None,
            None,
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

        # Been Verified data
        beenverified = {}

        if lead_details is None:
            birth_date = None
            age = None
            charges = None
            phone = None
            status = None
            notes = None
            email = None
            lead_details_dict = {}
            onabout_date = None
            name = None
        else:
            middle_name = (
                f", {case_details.middle_name},"
                if case_details.middle_name is not None
                else ","
            )
            name = f"{case_details.first_name}{middle_name}{case_details.last_name}"
            birth_date = case_details.birth_date
            age = lead_details.age
            charges = lead_details.charges_description
            phone = lead_details.phone
            if case_details.ticket is not None:
                onabout_date = case_details.ticket.get("client-birthdate")
            else:
                onabout_date = None
            if isinstance(phone, dict):
                if len(phone) > 0:
                    beenverified["phones"] = [
                        p.get("phone") for p in phone.values()
                    ]
                    phone = phone.get("0", {}).get("phone")
                else:
                    phone = None
            else:
                beenverified["phones"] = [
                    phone,
                ]
            beenverified["phones"] = [
                humanize_phone(p) for p in beenverified["phones"]
            ]
            email = lead_details.email
            if isinstance(email, dict):
                if len(email) > 0:
                    email = email.get("0", {}).get("address")
                else:
                    email = None
            status = lead_details.status
            notes = lead_details.notes
            lead_details_dict = lead_details.model_dump()

        if case_details is None:
            parties = pd.DataFrame(
                columns=[
                    "desc",
                    "formatted_partyname",
                    "formatted_telephone",
                    "formatted_partyaddress",
                ]
            )
            documents = pd.DataFrame(
                columns=["docket_desc", "file_path", "document_extension"]
            )
            filing_date = None
            case_type = None
            location = None
        else:
            parties = pd.DataFrame(case_details.parties)
            documents = pd.DataFrame(case_details.documents)
            filing_date = case_details.filing_date
            case_type = case_details.case_type
            location = case_details.location

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
                bucket.get_blob(x).generate_signed_url(
                    expiration=timedelta(seconds=3600)
                )
            )
        )

        try:
            media_url = documents[
                documents["Description"] == "Information Filed by Citation"
            ]["File Path"].values[0]
        except IndexError:
            media_url = None

        documents["File Path"] = documents["File Path"].apply(
            lambda x: (f"[Download]" f"({x})")
        )

        if media_url is not None:
            document_preview = dmc.Card(
                children=[
                    html.Iframe(
                        src=media_url,
                        style={
                            "width": "100%",
                            "height": "50%",
                            "min-height": "200px",
                        },
                    )
                ],
                shadow="sm",
            )
        else:
            document_preview = None

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
                            html.Td("Full Name", className="font-weight-bold"),
                            html.Td(name),
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
                            html.Td("Location", className="font-weight-bold"),
                            html.Td(location),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td("Type", className="font-weight-bold"),
                            html.Td(case_type),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td(
                                "On or About Date (Beta)",
                                className="font-weight-bold",
                            ),
                            html.Td(onabout_date),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td("Case Type", className="font-weight-bold"),
                            html.Td(case_type),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td(
                                "Case Status", className="font-weight-bold"
                            ),
                            html.Td(status),
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
                            html.Td(birth_date),
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
                            html.Td(humanize_phone(phone)),
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
                    lg=6,
                    xs=12,
                ),
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H3(
                                            "Documents", className="card-title"
                                        ),
                                        documents_ag_grid,
                                    ]
                                ),
                                className="mb-2",
                            ),
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H3(
                                            "Ticket", className="card-title"
                                        ),
                                        document_preview,
                                    ]
                                ),
                                className="mb-2",
                            ),
                        ]
                    ),
                    lg=6,
                    xs=12,
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
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H3(
                                "BeenVerified Details", className="card-title"
                            ),
                            html.H6("Details:"),
                            html.P(beenverified.get("details")),
                            html.H6("Phones:"),
                            html.P(", ".join(beenverified.get("phones", []))),
                        ]
                    ),
                    class_name="mb-2",
                ),
                lg=12,
                xs=12,
            ),
            lead_details_dict,
            phone,
            email,
            status,
            notes,
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


# Update the lead details when save button is clicked
@callback(
    Output("lead-single-save-status", "children"),
    Input("lead-single-save-button", "n_clicks"),
    State("case-id", "children"),
    State("lead-single-phone", "value"),
    State("lead-single-email", "value"),
    State("lead-single-status", "value"),
    State("lead-single-notes", "value"),
)
def update_lead_details(btn, case_id, phone, email, status, notes):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "lead-single-save-button":
        lead_details = {}
        lead_details["phone"] = phone
        lead_details["email"] = email
        lead_details["status"] = status
        lead_details["notes"] = notes
        leads.patch_lead(case_id, **lead_details)
        toast = build_toast(
            "Your modification was saved ✅", "Lead details updated"
        )
        return toast


@callback(
    Output("lead-single-letter-status", "children"),
    Input("lead-generate-pdf-button", "n_clicks"),
    State("case-id", "children"),
)
def generate_letter_pdf(btn, case_id):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "lead-generate-pdf-button":
        try:
            case_id = str(case_id)
            envelope_url, letter_url = letters.generate_letter(case_id)

            output = html.Div(
                [
                    html.H6(
                        "The letter was generated : ", className="card-title"
                    ),
                    # Small button
                    html.A(
                        "Download Envelope",
                        href=envelope_url,
                        target="_blank",
                        className="btn btn-primary m-1 btn-sm",
                    ),
                    html.A(
                        "Download Letter",
                        href=letter_url,
                        target="_blank",
                        className="btn btn-primary m-1 btn-sm",
                    ),
                    build_toast(
                        "Letter generated ✅",
                        "The letter was generated successfully",
                    ),
                ],
            )
            return output
        except Exception:
            toast = build_toast(
                "An error occurred ❌",
                "Letter could not be generated",
                color="danger",
            )
            return toast


@callback(
    Output("case-refresh-button-status", "children"),
    Input("case-refresh-button", "n_clicks"),
    State("case-id", "children"),
)
def refresh_case(btn, case_id):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "case-refresh-button":
        try:
            case_id = str(case_id)
            case_details = cases.get_single_case(case_id)
            case_net_account = get_account("case_net_missouri")
            case_net = CaseNet(
                url=case_net_account.url,
                username=case_net_account.username,
                password=case_net_account.password,
            )
            case_refreshed = case_net.refresh_case(case_details.model_dump())

            case_refreshed_obj = cases_model.Case.parse_obj(case_refreshed)

            cases.update_case(case_refreshed_obj)

            toast = build_toast(
                "The case was refreshed successfully" "Case refreshed ✅",
            )
            return toast
        except Exception as e:
            toast = build_toast(
                f"The case could not be refreshed {e}",
                "An error occurred ❌",
                color="danger",
            )
            return toast
