import logging

import dash
from dash import Input, Output, State, callback, ctx

from src.core.config import get_settings
from src.services import leads, messages

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
    Output("modal-content-sending-status", "children"),
    Input("send-all-cases", "n_clicks"),
    Input("modal-content", "children"),
    State("memory", "data"),
    State("lead-single-message-modal", "value"),
    State("lead-media-enabled-modal", "value"),
    running=[
        (Output("send-all-cases", "disabled"), True, False),
        (Output("send-all-cases-cancel", "disabled"), False, True),
    ],
    cancel=[Input("send-all-cases-cancel", "n_clicks")],
)
def send_many_message(*args, **kwargs):
    if ctx.triggered_id == "send-all-cases":
        df = ctx.states["memory.data"]["df"] or []
        template_msg = ctx.states["lead-single-message-modal.value"] or ""
        include_case_copy = (
            ctx.states["lead-media-enabled-modal.value"] or False
        )
        for case in df:
            # Dict keys to lower and replace spaces with underscores
            case = {k.lower().replace(" ", "_"): v for k, v in case.items()}

            # first_name and last_name should be capitalized
            case["first_name"] = case["first_name"].capitalize()
            case["last_name"] = case["last_name"].capitalize()

            case_id = case["case_index"]
            phone = case["phone"]
            try:
                # TODO: add a check validation of template sending SMS with the case data by Twilio
                sms_message = template_msg.format(**case)
                message_status = messages.send_message(
                    case_id,
                    sms_message,
                    phone,
                    media_enabled=include_case_copy,
                )

                if message_status == "queued" or message_status == "accepted":
                    leads.update_lead_status(case_id, "contacted")

            except Exception as e:
                logger.error(
                    f"An error occurred while sending the message. {e}"
                )
                return f"An error occurred while sending the message"
        return "Messages sent successfully"

    return ""
