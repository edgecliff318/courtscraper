import json
import logging

import dash_mantine_components as dmc
from dash import (
    ALL,
    MATCH,
    Input,
    Output,
    callback,
    callback_context,
    no_update,
)

from src.components.leads.lead import get_lead_card
from src.core.config import get_settings
from src.services import leads as leads_service

logger = logging.Logger(__name__)

settings = get_settings()


@callback(
    Output("leads-queue-grid", "children"),
    Input("court-selector", "value"),
)
def render_leads(court_code_list):
    leads_list = leads_service.get_last_lead(
        status="contacted",
        court_code_list=court_code_list,
        limit=10,
        search_limit=100,
    )

    return [
        dmc.Col(get_lead_card(lead), span=12, xs=12, sm=6, md=4, lg=4, xl=3)
        for lead in leads_list
    ]


@callback(
    Output({"type": "lead-output-id", "index": MATCH}, "children"),
    Input({"type": "notes", "index": MATCH}, "value"),
    Input({"type": "won-button", "index": MATCH}, "n_clicks"),
    Input({"type": "wait-button", "index": MATCH}, "n_clicks"),
    Input({"type": "lost-button", "index": MATCH}, "n_clicks"),
    Input({"type": "lead-phone-status", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def process_lead(*args):
    ctx = callback_context

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    inputs = ctx.inputs

    try:
        trigger_dict = json.loads(trigger)
        trigger = trigger_dict.get("type")
        lead_id = trigger_dict.get("index")
    except json.decoder.JSONDecodeError:
        return no_update

    if trigger == "notes":
        leads_service.patch_lead(lead_id, notes=inputs[trigger])

    if trigger == "won-button":
        leads_service.patch_lead(lead_id, status="won")

    if trigger == "wait-button":
        leads_service.patch_lead(lead_id, status="wait")

    if trigger == "lost-button":
        leads_service.patch_lead(lead_id, status="lost")

    if trigger == "lead-phone-status":
        leads_service.patch_lead(lead_id, phone_status=inputs[trigger])
