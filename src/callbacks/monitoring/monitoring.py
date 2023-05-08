import logging

import dash.html as html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback, html

from src.core.config import get_settings
from src.services import leads

logger = logging.Logger(__name__)

settings = get_settings()


@callback(
    Output("message-monitoring", "children"),
    # Input("monitoring-button", "n_clicks"),
    Input("court-selector", "value"),
    Input("date-selector", "start_date"),
    Input("date-selector", "end_date"),
    Input("monitoring-status-selector", "value"),
)
def render_status_msg(court_code_list, start_date, end_date, status):

    ## TODO: Read from DB from firebase and display in the grid
    ## NOTE: This is a dummy data
    grid = "Empty"
    status = None
    leads_list = leads.get_leads(court_code_list, start_date, end_date, status)
    df = pd.DataFrame([lead.dict() for lead in leads_list])
    cols = ["case_id", "case_date", "first_name", "last_name", "phone"]
    df = df[cols]
    df["smg_status"] = "Pending"
    df["sid"] = "mmfd33k4l3klkl32k4l324"
    df["created_at"] = "2021-01-01"
    df["retry_count"] = 0

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
    df = df.set_index("case_id")
    df = df.rename(
        columns={
            "first_name": "First Name",
            "last_name": "Last Name",
            "phone": "Phone",
            "smg_status": "Status",
            "sid": "SID",
            "created_at": "Sending At",
            "retry_count": "Retry Count",
            "case_id": "Case ID",
            "case_date": "Case Date",
        }
    )
    df.index.name = "Case ID"
    df.reset_index(inplace=True)

    column_defs = [
        {
            "headerName": "User Details",
            "children": [
                {
                    "headerName": col,
                    "field": col,
                    "editable": True,
                    "filter": "agTextColumnFilter",
                    "sortable": True,
                    "resizable": True,
                    "flex": 1,
                }
                for col in ["Case ID", "First Name", "Last Name", "Phone"]
            ],
        },
        {
            "headerName": "Message Results",
            "children": [
                {
                    "headerName": col,
                    "field": col,
                    "editable": True,
                    "filter": "agTextColumnFilter",
                    "sortable": True,
                    "resizable": True,
                    "flex": 1,
                }
                for col in ["Status", "Sending At", "Retry Count", "SID"]
            ],
        },
    ]

    grid = dag.AgGrid(
        id="portfolio-grid",
        columnDefs=column_defs,
        rowData=df.to_dict("records"),
        columnSize="autoSize",
        style={"height": 700},
        dashGridOptions={
            "undoRedoCellEditing": True,
            "rowSelection": "multiple",
            "rowMultiSelectWithClick": True,
        },
    )
    return [
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "SMS Monitoring",
                                    className="card-title m-1",
                                ),
                                html.Div(
                                    [
                                        dbc.Button(
                                            "Remove ",
                                            id="cases-process",
                                            className="card-title m-2",
                                        ),
                                        dbc.Button(
                                            "Resend",
                                            id="cases-process",
                                            className="card-title m-2",
                                        ),
                                    ],
                                    id="message-monitoring ",
                                ),
                            ],
                            className="d-flex justify-content-between",
                        ),
                        grid,
                    ]
                ),
            ),
            width=12,
            className="mb-2",
        )
    ]
