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
        if status == "all":
            status = None
        leads_list = leads.get_leads(
            court_code_list, start_date, end_date, status
        )
        df = pd.DataFrame([lead.dict() for lead in leads_list])

        if df.empty:
            return [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("Leads", className="card-title"),
                                "No leads found",
                            ]
                        ),
                    ),
                    width=12,
                    className="mb-2",
                )
            ]

        df["case_date"] = df["case_date"].dt.strftime("%m/%d/%Y")

        df = df[
            [
                "case_id",
                "case_date",
                "first_name",
                "last_name",
                "phone",
                "email",
                "status",
                "age",
                "charges",
                "disposition",
            ]
        ].set_index("case_id")

        df = df.rename(
            columns={
                "first_name": "First Name",
                "last_name": "Last Name",
                "phone": "Phone",
                "email": "Email",
                "status": "Status",
                "age": "Age",
                "charges": "Charges",
                "disposition": "Disposition",
                "case_date": "Date",
            }
        )
        df.index.name = "Case ID"

        results = tables.make_bs_table(df)
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
