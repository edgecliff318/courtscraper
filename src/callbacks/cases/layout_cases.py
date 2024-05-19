import logging

from dash import Input, Output, callback, ctx
import dash

from src.core.config import get_settings
from src.services import messages

logger = logging.Logger(__name__)

settings = get_settings()


@callback(
    Output("lead-single-message-selector-modal", "data"),
    Input("lead-single-message-modal", "value"),
)
def render_message_selector(*args):
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id.endswith("-modal"):
        messages_list = messages.get_messages_templates()
        options = [
            {"label": c.template_name, "value": c.template_id} for c in messages_list
        ]
        return options

    return dash.no_update


@callback(
    Output("lead-single-message-modal", "value"),
    Input("lead-single-message-selector-modal", "value"),
)
def render_selected_message_modal(message_id, *args):
    if message_id is None:
        return ""
    message_template = messages.get_single_message_template(message_id)
    message = message_template.template_text
    return message
