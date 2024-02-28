import logging

import dash
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, State, callback, dcc, html
from twilio.rest import Client

import src.services.cases as cases_service
from src.components.conversation import messaging_template
from src.core.config import get_settings
from src.services.participants import ParticipantsService

logger = logging.getLogger(__name__)
settings = get_settings()


@callback(
    Output("communication-participant-select", "data"),
    Output("communication-participant-select", "value"),
    Input("url", "pathname"),
    State("case-id", "children"),
)
def get_participants_list(url, case_id):
    case = cases_service.get_single_case(case_id)
    participants_service = ParticipantsService()
    participants_list = participants_service.get_items(
        id=case.participants, role="defendant"
    )

    if participants_list is None or len(participants_list) == 0:
        return dash.no_update, dash.no_update

    participants_data = [
        {
            "label": f"{p.role.capitalize()} - {p.first_name} {p.last_name}",
            "value": p.id,
        }
        for p in participants_list
    ]

    return participants_data, participants_list[0].id


# Callback for multiplage redirection when selecting the participant value
@callback(
    Output("communication-details", "children"),
    Output("communication-memory", "data"),
    Input("communication-participant-select", "value"),
    State("case-id", "children"),
)
def get_communication_details(participant_id, case_id):
    if participant_id is None:
        return dmc.Alert(
            "Please select a participant to view their communications",
            color="indigo",
        )
    participants_service = ParticipantsService()
    participant = participants_service.get_single_item(participant_id)

    if participant.phone is None and participant.email is None:
        return dmc.Alert(
            "No communication details found for this participant as "
            "no phone or email is available. Please add phone or email "
            "to the participant to view their communications.",
            color="indigo",
        )

    df = pd.DataFrame(
        [
            {
                "First Name": participant.first_name,
                "Last Name": participant.last_name,
                "Role": participant.role,
                "Email": participant.email,
                "Phone": participant.phone,
                "SID": participant.id,
                "Case ID": case_id,
                "case_index": case_id,
            }
        ]
    )

    prefix = "communication"

    messages_module = html.Div(
        messaging_template(df, prefix="communication", many_responses=True),
        id=f"{prefix}-modal-content",
    )

    modal_footer_buttons = [
        dmc.Button(
            text,
            id=f"{prefix}-{button_id}",
            className="ml-auto",
            color=color,
            display="block" if button_id == "send-all" else "none",
        )
        for text, button_id, color in [
            ("Update Status", "modal-lead-status-update", "dark"),
            ("Generate Letters", "generate-letters", "dark"),
            ("Send ", "send-all", "green"),
            ("Cancel", "all-cancel", "red"),
        ]
    ]
    data = {"df": df.to_dict("records")}

    messaging_content = dmc.Stack(
        [
            dmc.Title(
                f"Communications for {participant.first_name} {participant.last_name}",
                order=4,
            ),
            messages_module,
            html.Div(id=f"{prefix}-hidden-div", style={"display": "none"}),
            html.Div(id=f"{prefix}-modal-lead-status-update-status"),
            html.Div(
                id=f"{prefix}-modal-content-generate-letters-status",
                className="m-2",
            ),
            dmc.Group(modal_footer_buttons),
        ]
    )

    return (
        messaging_content,
        data,
    )
