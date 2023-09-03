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

logger = logging.getLogger(__name__)
settings = get_settings()


def send_to_client(email, subject, message, attachments):
    intercom = IntercomConnector(settings.INTERCOM_API_KEY)

    contact = intercom.search_contact(email="shawn@tickettakedown.com")
    admins = intercom.get_admins()

    output = intercom.send_message(
        sender=admins[0],
        contact=contact,
        message=message,
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

    params = get_email_params(template, trigger, case_id, states, inputs)
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

    trigger = ctx.triggered[0]["prop_id"]
    states = ctx.states
    inputs = ctx.inputs

    document_preview = get_preview(
        template,
        trigger,
        case_id,
        states,
        inputs,
        file_content,
        filename,
        role="client",
    )
    # Put the attachements in a multi select
    # and add a button to upload the attachments

    return document_preview


@callback(
    output=Output("modal-client-response", "children"),
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
    if ctx.triggered[0]["prop_id"] == "modal-client-submit.n_clicks":
        return send_email(
            template,
            "modal-client-submit",
            case_id,
            ctx.states,
            ctx.inputs,
            send_to_client,
        )
