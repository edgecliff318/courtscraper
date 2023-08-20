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
    Input("leads-queue-refresh", "children"),
    Input("leads-status", "value"),
)
def render_leads(court_code_list, _, status):
    leads_list = leads_service.get_last_lead(
        status=status,
        court_code_list=court_code_list,
        limit=1,
        search_limit=100,
    )

    if leads_list is None:
        return "No leads found."

    if not isinstance(leads_list, list):
        leads_list = [leads_list]

    if len(leads_list) == 0:
        return no_update

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
    trigger_value = ctx.triggered[0]["value"]

    try:
        trigger_dict = json.loads(trigger)
        trigger = trigger_dict.get("type")
        lead_id = trigger_dict.get("index")
    except json.decoder.JSONDecodeError:
        return no_update

    if trigger == "notes":
        leads_service.patch_lead(lead_id, notes=trigger_value)
        return no_update

    if trigger == "won-button":
        leads_service.patch_lead(lead_id, status="won")
        return "won"

    if trigger == "wait-button":
        leads_service.patch_lead(lead_id, status="wait")
        return "wait"

    if trigger == "lost-button":
        leads_service.patch_lead(lead_id, status="lost")
        return "lost"

    return no_update


@callback(
    Output("leads-queue-refresh", "children"),
    Input({"type": "lead-output-id", "index": ALL}, "children"),
)
def refresh_leads(*args):
    return True


@callback(
    Output("leads-queue-phone-update", "children"),
    Input({"type": "lead-phone-status", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def update_phone(*args):
    ctx = callback_context

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    trigger_value = ctx.triggered[0]["value"]
    if trigger_value is None or trigger_value == "":
        return no_update

    try:
        trigger_dict = json.loads(trigger)
        trigger = trigger_dict.get("type")
        lead_id, phone_id = trigger_dict.get("index").split("-")
    except json.decoder.JSONDecodeError:
        return no_update

    if trigger == "lead-phone-status":
        lead = leads_service.get_single_lead(lead_id)
        if lead is None:
            raise ValueError("Lead is None")
        if lead.phone is None:
            raise ValueError("Lead phone is None")

        if isinstance(lead.phone, str):
            raise ValueError("Lead phone is str")

        lead.phone[phone_id]["state"] = trigger_value

        leads_service.patch_lead(lead_id, phone=lead.phone)
