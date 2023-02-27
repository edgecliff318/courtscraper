import logging

from dash import Input, Output, callback

from src.core.config import get_settings
from src.services import messages

logger = logging.Logger(__name__)

settings = get_settings()


@callback(
    Output("lead-single-message-selector", "options"),
    Input("url", "pathname"),
    Input("lead-single-case-details", "data"),
)
def render_message_selector(pathname, case_details):
    if case_details is None:
        case_details = dict()
    messages_list = messages.get_messages_templates()
    options = [
        {
            "label": c.template_name,
            "value": c.template_text.replace(
                "{first_name}", case_details.get("first_name", "{first_name}").title()
            ),
        }
        for c in messages_list
    ]
    return options


@callback(
    Output("lead-single-message", "value"),
    Input("lead-single-message-selector", "value"),
)
def render_selected_message(message):
    return message
