import logging

from dash import Input, Output, callback

from src.core.config import get_settings
from src.services import messages

logger = logging.Logger(__name__)

settings = get_settings()


@callback(
    Output("lead-single-message-selector", "options"),
    Input("case-id", "children"),
)
def render_message_selector(case_id):
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
    Output("lead-single-message", "value"),
    Output("lead-media-enabled", "value"),
    Input("lead-single-message-selector", "value"),
    Input("lead-single-case-details", "data"),
)
def render_selected_message(message_id, case_details):
    if message_id is None:
        return "", False
    if case_details is None:
        case_details = dict()
    message_template = messages.get_single_message_template(message_id)
    message = message_template.template_text.replace(
        "{first_name}",
        case_details.get("first_name", "there").title(),
    )
    return message, message_template.media_enabled
