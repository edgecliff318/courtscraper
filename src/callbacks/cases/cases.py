import logging
import typing as t

import dash
import diskcache
import dash.html as html
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, ctx, DiskcacheManager, State

from src.core.config import get_settings
from src.models import messages as messages_model
from src.services import cases, leads, messages

logger = logging.Logger(__name__)

settings = get_settings()

cache = diskcache.Cache("./.cache")
background_callback_manager = DiskcacheManager(cache)


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
    State('memory', 'data'),
    Input("lead-single-message-modal", "value"),
    Input("lead-media-enabled-modal", "value"),
    

    background=True,
    manager=background_callback_manager,

)
def send_many_message(_, data: t.Dict , template: str, case_copy : bool):
    
    if ctx.triggered_id == "send-all-cases":
    # return #, False 
        return f"your operation is on progress {str(data), str(template)}   copy: {str(case_copy)}"
    return dash.no_update
