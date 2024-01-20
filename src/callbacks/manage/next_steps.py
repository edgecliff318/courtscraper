import logging

import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, callback

from src.components.cases.next_steps import get_next_step_modal_content
from src.components.cases.status import case_statuses
from src.core.config import get_settings
from src.models.cases import Case
from src.services import cases as cases_service
from src.services import messages
from src.services.participants import ParticipantsService

logger = logging.getLogger(__name__)
settings = get_settings()


def get_defendent(case: Case):
    # Get the list of participants
    participants_service = ParticipantsService()

    if case.participants is None or len(case.participants) == 0:
        raise ValueError(
            "No participants found ! Please add participants to the case",
        )

    participants_list = participants_service.get_items(
        id=case.participants, role="defendant"
    )

    if len(participants_list) == 0:
        raise ValueError("No participants found")
    if len(participants_list) > 1:
        raise ValueError("Multiple participants found")

    participant = participants_list[0]

    return participant


@callback(
    Output("modal-next-step", "opened"),
    Output("modal-next-step", "children"),
    Input("modal-next-step-trigger", "data"),
    Input("modal-next-step-close-button", "n_clicks"),
    Input("update-status-button", "n_clicks"),
    prevent_initial_call=True,
)
def modal_next_step(data, n_clicks_close, n_clicks_update_status):
    ctx = dash.callback_context
    trigger_id = ctx.triggered_id

    if trigger_id == "modal-next-step-close-button":
        return False, dash.no_update

    if data is None and trigger_id != "update-status-button":
        return dash.no_update, dash.no_update

    if data is None:
        data = {}

    suggested_next_step = data.get("next_step")
    message = data.get("message")
    send_sms = data.get("send_sms", False)

    options = [
        {
            "label": status_details.get("label"),
            "value": status_id,
        }
        for status_id, status_details in case_statuses.items()
    ]

    output = get_next_step_modal_content(
        status_options=options,
        status_value=suggested_next_step,
        message=message,
        send_sms=send_sms,
    )
    return True, output


@callback(
    Output("modal-next-step-output", "children"),
    Input("modal-next-step-submit-button", "n_clicks"),
    State("modal-next-step-status", "value"),
    State("modal-next-step-sms", "checked"),
    State("modal-next-step-message", "value"),
    State("case-id", "children"),
    prevent_initial_call=True,
)
def modal_next_step_submit(
    n_clicks,
    status,
    send_sms,
    message,
    case_id,
):
    if n_clicks is None:
        return dash.no_update

    # Get the participant id from the URL
    case = cases_service.get_single_case(case_id)

    if case is None:
        return dmc.Alert(
            "No case found",
            color="red",
            title="No case found",
        )

    participant = get_defendent(case)

    # Updating the case
    cases_service.patch_case(case_id, {"status": status})

    alert_message = "Case updated successfully"

    # Sending the SMS Message
    if send_sms:
        phone = participant.phone
        if phone is None:
            return dmc.Alert(
                "No phone number found for the participant",
                color="red",
                title="No phone number found",
            )

        messages.send_message(
            case_id,
            message,
            phone,
            force_send=True,
        )
        alert_message = "Case updated successfully and SMS sent"

    return dmc.Alert(
        alert_message,
        color="green",
        title="Case updated",
    )
