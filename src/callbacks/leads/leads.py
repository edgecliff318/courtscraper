import logging

import dash
import dash.html as html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, html, dcc, ctx, callback

from src.components.inputs import generate_form_group


from src.core.config import get_settings
from src.services import leads

logger = logging.Logger(__name__)

settings = get_settings()


@callback(
    Output("leads-data", "children"),
    # Input("leads-button", "n_clicks"),
    Input("court-selector", "value"),
    Input("date-selector", "start_date"),
    Input("date-selector", "end_date"),
    Input("lead-status-selector", "value"),
)
def render_leads( court_code_list, start_date, end_date, status):
    grid = "Empty"
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
    df.reset_index(inplace=True)
    df["Case ID"] = df["Case ID"].map(lambda x: f"[{x}](/case/{x})")
    column_defs = [
        {
            "headerName": "Case ID",
            "field": "Case ID",
            "editable": False,
            "filter": "agTextColumnFilter",
            "sortable": True,
            "resizable": True,
            "flex": 1,
            "cellRenderer": "markdown",
        }
    ] + [
        {
            "headerName": col,
            "field": col,
            "editable": True,
            "filter": "agTextColumnFilter",
            "sortable": True,
            "resizable": True,
            "flex": 1,
        }
        for col in df.columns
        if col not in  ["Case ID", "Phone", "Email", "Status"]
    ]
    column_defs += [
        {
            "headerName": col,
            "field": col,
            "editable": True,
            "filter": "agTextColumnFilter",
            "sortable": True,
            "resizable": True,
            "flex": 1,
        }
        for col in ["Phone", "Email", "Status"]
    ] 
    grid = dag.AgGrid(
        id="portfolio-grid",
        columnDefs=column_defs,
        rowData=df.to_dict("records"),
        columnSize="autoSize",
        style={"height": 700},
        dashGridOptions={
            "undoRedoCellEditing": True,
            "rowSelection": "single",
            "rowSelection":"multiple", "rowMultiSelectWithClick": True,
        },
    )
    return [
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div([html.H3("Cases", className="card-title"),dbc.Button("Cases Process", id="cases-process", className="card-title")], className="d-flex justify-content-between"),
                       
                        grid,
                    ]
                ),
            ),
            width=12,
            className="mb-2",
        )

    ]


