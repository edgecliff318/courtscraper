import logging
import typing as t
import time


import dash
import diskcache
import dash.html as html
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, ctx, State

from src.core.config import get_settings
from src.models import messages as messages_model
from src.services import cases, leads, messages

logger = logging.Logger(__name__)

settings = get_settings()


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



@callback(
    Output("send-all-cases", "disabled"),
    Output("modal-content-sending-status", "children"),
    Input("send-all-cases", "n_clicks"),
    Input("modal", "is_open"),
)
def send_many_message(*args, **kwargs):
    if ctx.triggered_id == "send-all-cases":
       return True, dbc.Alert("Sending messages in progress", color="success")
    return False, ""

@callback(
    Output("send-of-all", "children"),
    Input("send-all-cases", "n_clicks"),
    State("memory", "data"),
    Input("lead-single-message-modal", "value"),
    Input("lead-media-enabled-modal", "value"),
    background=True,
    # running=[
    #     (Output("modal-content-sending-status", "children"), "start", dbc.Alert("Sending messages in progress", color="success")),
    # ],
)
def send_many_message(*args, **kwargs):
    if ctx.triggered_id == "send-all-cases":
        df = ctx.states["memory.data"]["df"] or []
        template_msg = ctx.inputs["lead-single-message-modal.value"] or ""
        include_case_copy = ctx.inputs["lead-media-enabled-modal.value"] or False
        ctx.outputs["modal-content-sending-status.children"] = "Sending messages in progress"
        for case in df:
            case_id = case["case_id"]
            phone = case["phone"]
            try:
                ## TODO: add a check validation of template sending SMS with the case data by Twilio
                sms_message = template_msg.format(**case)
                messages.send_message(
                    case_id, sms_message , phone, media_enabled=include_case_copy
                )
            except Exception as e:
                logger.error(f"An error occurred while sending the message. {e}")
                return f"An error occurred while sending the message. {e}"

    return dash.no_update
