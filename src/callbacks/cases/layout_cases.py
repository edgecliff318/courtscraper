import logging

from dash import Input, Output, callback , State

from src.core.config import get_settings
from src.services import messages

logger = logging.Logger(__name__)

settings = get_settings()


@callback(
    Output("lead-single-message-selector-modal", "options"),
    Input("modal", "children"),
)
def render_message_selector(_):
    messages_list = messages.get_messages_templates()
    options = [
        {
            "label": c.template_name,
            "value": c.template_id,
        }
        for c in messages_list
    ]
    return options


@callback(
    Output("lead-single-message-modal", "value"),
    Input("lead-single-message-selector-modal", "value"),
)
def render_selected_message_modal(message_id):#, case_details):
    if message_id is None:
        return ""
    message_template = messages.get_single_message_template(message_id)
    message = message_template.template_text    
    return message
