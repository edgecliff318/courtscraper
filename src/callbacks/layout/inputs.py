import logging

from dash import Input, Output, callback

from src.services import courts

logger = logging.Logger(__name__)


@callback(
    Output("court-selector", "data"),
    Input("url", "pathname"),
)
def render_content_persona_details_selector(pathname):
    courts_list = courts.get_courts()
    options = [{"label": c.name, "value": c.code} for c in courts_list]
    return options
