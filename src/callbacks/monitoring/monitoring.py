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
    Output("message-monitoring", "children"),
    Input("monitoring-button", "n_clicks"),
    Input("court-selector", "value"),
    Input("date-selector", "start_date"),
    Input("date-selector", "end_date"),
    Input("monitoring-status-selector", "value"),
)
# def render_leads(search, court_code_list, start_date, end_date, status):
def render_leads(*args):
    print(args, "clilc \n\n\n\n")
   
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    grid = "Empty"
    # if trigger_id == "leads-button":
    if 1 == 1:
        
        # leads_list = leads.get_leads(
        #     court_code_list, start_date, end_date, status
        # )
        # df = pd.DataFrame([lead.di÷ct() for lead in leads_list])
        df = pd.read_csv(
            "https://raw.githubusercontent.com/plotly/datasets/master/ag-grid/olympic-winners.csv"
        )

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

        



        columnDefs = [
            {
                "headerName": "User Details",
                "children": [
                    {
                        "field": "athlete",
                        "width": 180,
                        "filter": "agTextColumnFilter",
                    },
                    {
                        "field": "age",
                        "width": 90,
                        "filter": "agNumberColumnFilter",
                    },
                    {"headerName": "Country", "field": "country", "width": 140},
                ],
            },
            {
                "headerName": "Message Results",
                "children": [
                    {"field": "sport", "width": 140},
                    {
                        "columnGroupShow": "closed",
                        "field": "total",
                        "width": 100,
                        "filter": "agNumberColumnFilter",
                    },
                    {
                        "columnGroupShow": "open",
                        "field": "gold",
                        "width": 100,
                        "filter": "agNumberColumnFilter",
                    },
                    {
                        "columnGroupShow": "open",
                        "field": "silver",
                        "width": 100,
                        "filter": "agNumberColumnFilter",
                    },
                    {
                        "columnGroupShow": "open",
                        "field": "bronze",
                        "width": 100,
                        "filter": "agNumberColumnFilter",
                    },
                ],
            },
        ]

        defaultColDef = {"resizable": True, "initialWidth": 200, "filter": True}

        grid = html.Div(
            [
                dcc.Markdown("Demonstration column groups."),
                dag.AgGrid(
                    columnDefs=columnDefs,
                    rowData=df.to_dict("records"),
                    defaultColDef=defaultColDef,
                ),
            ]
        )

    return [
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        # html.Div([html.H3("Cases", className="card-title"),dbc.Button("Cases Process", id="cases-process", className="card-title")], className="d-flex justify-content-between"),
                       
                        grid,
                    ]
                ),
            ),
            width=12,
            className="mb-2",
        )

    ]

