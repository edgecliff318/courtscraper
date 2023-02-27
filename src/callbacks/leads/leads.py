import logging

import dash
import dash.html as html
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback

from src.components import tables
from src.core.config import get_settings
from src.services import leads

logger = logging.Logger(__name__)

settings = get_settings()


@callback(
    Output("leads-data", "children"),
    Input("leads-button", "n_clicks"),
    Input("court-selector", "value"),
    Input("date-selector", "start_date"),
    Input("date-selector", "end_date"),
    Input("lead-status-selector", "value"),
)
def render_leads(search, court_code_list, start_date, end_date, status):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    results = "Empty"
    if trigger_id == "leads-button":
        leads_list = leads.get_leads(court_code_list, start_date, end_date, status)
        df = pd.DataFrame([l.dict() for l in leads_list])

        results = tables.make_bs_table(
            df[
                [
                    "case_id",
                    "creation_date",
                    "first_name",
                    "last_name",
                    "phone",
                    "email",
                    "status",
                    "age",
                    "charges",
                ]
            ].set_index("caseNumber")
        )
    return [
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H3("Cases", className="card-title"),
                        results,
                    ]
                ),
            ),
            width=12,
            className="mb-2",
        )
    ]
