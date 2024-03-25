import logging

import dash
from dash import ALL, Input, Output, State, callback

from src.components.cases.workflow.email import (
    get_email_params,
    get_preview,
    send_email,
)
from src.connectors.intercom import IntercomConnector
from src.core.config import get_settings
from src.services import mycase as mycase_service
from src.services import templates as templates_service

logger = logging.getLogger(__name__)
settings = get_settings()


def send_to_client_intercom(
    email, subject, message, attachments, case_id=None
):
    intercom = IntercomConnector(settings.INTERCOM_API_KEY)

    if email is None:
        raise Exception("Please set the email address of the client.")

    contact = intercom.search_contact(email=email.lower())

    if contact is None:
        intercom.create_contact(email=email.lower())
        contact = intercom.search_contact(email=email.lower())

    admins = intercom.get_admins()
    sender = None
    for admin in admins:
        if admin.get("email") == settings.INTERCOM_SENDER_ID:
            sender = admin
            break

    output = intercom.send_message(
        sender=sender,
        contact=contact,
        message=message,
        subject=subject,
    )

    return output


@callback(
    Output("modal-client-preview-parameters", "children"),
    Input("modal-client-preview", "opened"),
    Input("modal-client-preview-generate", "n_clicks"),
    Input("section-client-select-template", "value"),
    State({"type": "modal-client-pars", "index": ALL}, "value"),
    State("case-id", "children"),
    prevent_initial_call=True,
)
def modal_client_pars(opened, update, template, pars, case_id):
    ctx = dash.callback_context
    if opened is False or opened is None:
        return dash.no_update

    if template is None:
        return "Please select a template", dash.no_update

    trigger = ctx.triggered[0]["prop_id"]
    inputs = ctx.inputs
    states = ctx.states

    params = get_email_params(
        template, trigger, case_id, states, inputs, include_invoice=True
    )
    return params


@callback(
    Output("modal-client-preview-content", "children"),
    Input("modal-client-preview", "opened"),
    Input({"type": "modal-client-pars", "index": ALL}, "value"),
    Input({"type": "modal-client-pars", "index": "upload"}, "contents"),
    Input({"type": "modal-client-pars", "index": ALL}, "n_clicks"),
    Input("section-client-select-template", "value"),
    State({"type": "modal-client-pars", "index": "upload"}, "filename"),
    State("case-id", "children"),
    prevent_initial_call=True,
)
def modal_client_preview(
    opened, pars, file_content, clicks, template, filename, case_id
):
    ctx = dash.callback_context
    if opened is False or opened is None:
        return dash.no_update

    if template is None:
        return "Please select a template", dash.no_update

    trigger_id = ctx.triggered_id
    states = ctx.states
    inputs = ctx.inputs

    document_preview = get_preview(
        template,
        trigger_id,
        case_id,
        states,
        inputs,
        file_content,
        filename,
        role="client",
        include_invoice=True,
    )
    # Put the attachements in a multi select
    # and add a button to upload the attachments

    return document_preview


@callback(
    output=[
        Output("modal-client-response", "children"),
        Output("modal-next-step-trigger", "data", allow_duplicate=True),
    ],
    inputs=[
        Input("modal-client-submit", "n_clicks"),
        State({"type": "modal-client-pars", "index": ALL}, "value"),
        State("case-id", "children"),
        State("section-client-select-template", "value"),
    ],
    running=[
        (Output("modal-client-submit", "disabled"), True, False),
        (Output("modal-client-cancel", "disabled"), False, True),
        (
            Output("modal-client-response", "style"),
            {"visibility": "hidden"},
            {"visibility": "visible"},
        ),
        (
            Output("modal-client-submit", "loading"),
            True,
            False,
        ),
    ],
    cancel=[Input("modal-client-cancel", "n_clicks")],
    prevent_initial_call=True,
    background=False,
)
def modal_client_submit(n_clicks, pars, case_id, template):
    ctx = dash.callback_context
    if (
        ctx.triggered[0]["prop_id"] == "modal-client-submit.n_clicks"
        and template is not None
    ):
        attachments = ctx.states.get(
            '{{"index":"attachments","type":"modal-client-pars"}}.value',
            [],
        )
        output, message = send_email(
            template=template,
            trigger="modal-client-submit",
            case_id=case_id,
            states=ctx.states,
            inputs=ctx.inputs,
            attachments=attachments,
            send_function=mycase_service.send_to_client_mycase,
            role="client",
            include_invoice=True,
        )
        output = True
        if output is True:
            template_details = templates_service.get_single_template(template)
            next_step = {
                "message": template_details.sms_message,
                "send_sms": template_details.sms,
                "next_case_status": template_details.next_case_status,
            }
            return message, next_step
        else:
            return message, dash.no_update

    return dash.no_update, dash.no_update
