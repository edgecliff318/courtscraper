import logging


import dash
import dash_mantine_components as dmc
from dash import Input, Output, callback, dcc
from src.models import participants


import src.services.cases as cases_service
from src.core.config import get_settings
import src.models as models
from src.services.participants import ParticipantsService

logger = logging.getLogger(__name__)
settings = get_settings()


@callback(
    Output("participants-list", "data"),
    Input("url", "pathname"),
)
def get_participants_list(url):
    participants_service = ParticipantsService()

    participants_all = participants_service.get_items()

    participants_data = [
        {"label": f"{p.role} - {p.first_name} {p.last_name}", "value": p.id}
        for p in participants_all
    ]

    return participants_data


# Callback for multiplage redirection when selecting the participant value
@callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("participants-list", "value"),
    prevent_initial_call=True,
)
def goto_participant(participant_id):
    if participant_id is None:
        return dash.no_update
    return f"/manage/participants/{participant_id}"
