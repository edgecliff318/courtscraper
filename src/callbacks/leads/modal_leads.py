import logging

import dash
import dash.html as html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, ctx
import dash_mantine_components as dmc

from src.components.inputs import generate_form_group
from src.components.conversation import messaging_template
from src.core.config import get_settings
from src.components.conversation import messaging_template
import re
from src.services import messages as messages_service

logger = logging.Logger(__name__)

settings = get_settings()


def handle_modal(prefix):
    @callback(
        Output(f"{prefix}-modal", "is_open"),
        Output(f"{prefix}-modal-content", "children"),
        Output(f"{prefix}-memory", "data"),
        State(f"{prefix}-memory", "data"),
        Input(f"{prefix}-data-grid", "selectedRows"),  
        Input(f"{prefix}-send-all", "n_clicks"),
        Input(f"{prefix}-response-many", "n_clicks"),
        Input("leads-data", "children"),
        prevent_initial_call=False,
    )
    def open_modal(data, selection, *args, **kwargs):
        triggered_id = ctx.triggered_id if ctx.triggered_id else ""

        if selection and (triggered_id == f"{prefix}-response-many"):
            df = pd.DataFrame(selection)
            # df_filter = df[["First Name", "Last Name", "Phone"]]
            # df_filter = df[[ "Phone"]]
            data = (
                {"df": df.to_dict("records")}
                if data is None
                else {"df": df.to_dict("records")}
            )
            return True, messaging_template(df, prefix), data

        return dash.no_update, dash.no_update, dash.no_update


for prefix in ["outbound", "monitoring" ]:
    handle_modal(prefix)






@callback(
        Output("conversation-modal", "is_open"),
        Output("conversation-modal-content", "children"),
        Output("conversation-memory", "data"),
        State("conversation-memory", "data"),
        Input("monitoring-data-grid", "selectedRows"),  
        Input("monitoring-send-all", "n_clicks"),
        Input("conversation-response-many", "n_clicks"),
        Input("leads-data", "children"),
        prevent_initial_call=False,
    )
def open_modal(data, selection, *args, **kwargs):
    triggered_id = ctx.triggered_id if ctx.triggered_id else ""
    if selection and (triggered_id == "conversation-response-many"):
        df = pd.DataFrame(selection)
        # df_filter = df[["First Name", "Last Name", "Phone"]]
        df_filter = df[[ "Phone"]]
        data = (
            {"df": df.to_dict("records")}
            if data is None
            else {"df": df.to_dict("records")}
        )
        return True, messaging_template(df, prefix), data
    return dash.no_update, dash.no_update, dash.no_update
