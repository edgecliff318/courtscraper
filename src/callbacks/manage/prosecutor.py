import logging

import dash
from dash import ALL, Input, Output, State, callback
from flask import session
from google.cloud.storage.retry import DEFAULT_RETRY

from src.components.cases.workflow.email import (
    get_email_params,
    get_preview,
    send_email,
)
from src.core.config import get_settings
from src.db import bucket
from src.services.emails import GmailConnector

logger = logging.getLogger(__name__)
settings = get_settings()


def send_to_prosecutor(email, subject, message, attachments, case_id=None):
    user_id = session.get("profile", {}).get("name", None)

    if user_id is None:
        # Redirect to login page
        return dash.no_update

    gmail_connector = GmailConnector(user_id=user_id)

    # Download attachments from the blob storage
    local_attachments = []
    for attachment in attachments:
        # Download the file locally
        blob = bucket.get_blob(attachment)
        if blob is None:
            logger.error(f"Blob {attachment} not found")
            continue
        # PDF File:
        output_filepath_pdf = settings.DATA_PATH.joinpath("tmp", blob.name)
        output_filepath_pdf.parent.mkdir(parents=True, exist_ok=True)

        modified_retry = DEFAULT_RETRY.with_delay(
            initial=1.5, multiplier=1.2, maximum=45.0
        )

        blob.download_to_filename(
            output_filepath_pdf, retry=modified_retry, timeout=20
        )
        local_attachments.append(output_filepath_pdf)

    return gmail_connector.send_email(
        subject=subject,
        message=message,
        to=email,
        attachments=local_attachments,
    )


@callback(
    Output("modal-prosecutor-preview-parameters", "children"),
    Input("modal-prosecutor-preview", "opened"),
    Input("modal-prosecutor-preview-generate", "n_clicks"),
    Input("section-prosecutor-select-template", "value"),
    State({"type": "modal-prosecutor-pars", "index": ALL}, "value"),
    State("case-id", "children"),
    prevent_initial_call=True,
)
def modal_prosecutor_pars(opened, update, template, pars, case_id):
    ctx = dash.callback_context
    if opened is False or opened is None:
        return dash.no_update

    if template is None:
        return "Please select a template", dash.no_update

    trigger = ctx.triggered[0]["prop_id"]
    inputs = ctx.inputs
    states = ctx.states

    params = get_email_params(
        template, trigger, case_id, states, inputs, role="prosecutor"
    )

    return params


@callback(
    Output("modal-prosecutor-preview-content", "children"),
    Input("modal-prosecutor-preview", "opened"),
    Input({"type": "modal-prosecutor-pars", "index": ALL}, "value"),
    Input({"type": "modal-prosecutor-pars", "index": "upload"}, "contents"),
    Input({"type": "modal-prosecutor-pars", "index": ALL}, "n_clicks"),
    Input("section-prosecutor-select-template", "value"),
    State({"type": "modal-prosecutor-pars", "index": "upload"}, "filename"),
    State("case-id", "children"),
    prevent_initial_call=True,
)
def modal_prosecutor_preview(
    opened, pars, file_content, clicks, template, filename, case_id
):
    ctx = dash.callback_context
    if opened is False or opened is None:
        return dash.no_update

    if template is None:
        return "Please select a template", dash.no_update
    triggered_id = ctx.triggered_id
    states = ctx.states
    inputs = ctx.inputs

    document_preview = get_preview(
        template,
        triggered_id,
        case_id,
        states,
        inputs,
        file_content,
        filename,
        role="prosecutor",
    )
    # Put the attachements in a multi select
    # and add a button to upload the attachments

    return document_preview


@callback(
    output=[
        Output("modal-prosecutor-response", "children"),
        Output("modal-next-step-trigger", "data", allow_duplicate=True),
    ],
    inputs=[
        Input("modal-prosecutor-submit", "n_clicks"),
        State({"type": "modal-prosecutor-pars", "index": ALL}, "value"),
        State("case-id", "children"),
        State("section-prosecutor-select-template", "value"),
        State("modal-prosecutor-force-send", "checked"),
    ],
    running=[
        (Output("modal-prosecutor-submit", "disabled"), True, False),
        (Output("modal-prosecutor-cancel", "disabled"), False, True),
        (
            Output("modal-prosecutor-response", "style"),
            {"visibility": "hidden"},
            {"visibility": "visible"},
        ),
        (
            Output("modal-prosecutor-submit", "loading"),
            True,
            False,
        ),
    ],
    cancel=[Input("modal-prosecutor-cancel", "n_clicks")],
    prevent_initial_call=True,
    background=False,
)
def modal_prosecutor_submit(n_clicks, pars, case_id, template, force_send):
    ctx = dash.callback_context
    if (
        ctx.triggered[0]["prop_id"] == "modal-prosecutor-submit.n_clicks"
        and template is not None
    ):
        attachments = ctx.states.get(
            '{"index":"attachments","type":"modal-prosecutor-pars"}.value',
            [],
        )
        output, message = send_email(
            template=template,
            trigger="modal-client-submit",
            case_id=case_id,
            states=ctx.states,
            inputs=ctx.inputs,
            send_function=send_to_prosecutor,
            attachments=attachments,
            role="prosecutor",
            force_send=force_send,
        )
        return message, {"next_step": "modal-prosecutor-submit"}

    return dash.no_update, dash.no_update
