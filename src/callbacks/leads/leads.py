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
    Output("leads-data", "children"),
    Input("court-selector", "value"),
    Input("date-selector", "start_date"),
    Input("date-selector", "end_date"),
    Input("lead-status-selector", "value"),
)
def render_leads(court_code_list, start_date, end_date, status):
    grid = "Empty"
    if status == "all":
        status = None
    leads_list = leads.get_leads(court_code_list, start_date, end_date, status)
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
            "charges_description",
            "disposed",
            "year_of_birth",
        ]
    ].set_index("case_id")

    df["case_index"] = df.index

    df = df.rename(
        columns={
            "first_name": "First Name",
            "last_name": "Last Name",
            "phone": "Phone",
            "email": "Email",
            "status": "Status",
            "age": "Age",
            "charges_description": "Charges",
            "disposed": "Disposed",
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
        },
        {
            # Hidden case id column
            "headerName": "case_index",
            "field": "case_index",
            "hide": True,
        },
        {
            "headerName": "Date",
            "field": "Date",
            "editable": False,
            "filter": "agTextColumnFilter",
            "sortable": True,
            "resizable": True,
            "flex": 1,
        },
        {
            "headerName": "First Name",
            "field": "First Name",
            "editable": False,
            "filter": "agTextColumnFilter",
            "sortable": True,
            "resizable": True,
            "flex": 1,
        },
        {
            "headerName": "Last Name",
            "field": "Last Name",
            "editable": False,
            "filter": "agTextColumnFilter",
            "sortable": True,
            "resizable": True,
            "flex": 1,
        },
        {
            "headerName": "Charges",
            "field": "Charges",
            "editable": False,
            "filter": "agTextColumnFilter",
            "sortable": True,
            "resizable": True,
            "flex": 2,
        },
        {
            "headerName": "Phone",
            "field": "Phone",
            "editable": False,
            "filter": "agTextColumnFilter",
            "sortable": True,
            "resizable": True,
            "flex": 1,
        },
        {
            "headerName": "Email",
            "field": "Email",
            "editable": False,
            "filter": "agTextColumnFilter",
            "sortable": True,
            "resizable": True,
            "flex": 1,
        },
        {
            "headerName": "Status",
            "field": "Status",
            "editable": False,
            "filter": "agTextColumnFilter",
            "sortable": True,
            "resizable": True,
            "flex": 1,
        },
        {
            "headerName": "Age",
            "field": "Age",
            "editable": False,
            "filter": "agNumberColumnFilter",
            "sortable": True,
            "resizable": True,
            "flex": 1,
        },
        # Show the disposed as badge
        {
            "headerName": "Disposed",
            "field": "Disposed",
            "editable": False,
            "filter": "agTextColumnFilter",
            "sortable": True,
            "resizable": True,
            "flex": 1,
            "cellRenderer": "badgeRenderer",
        },
        {
            # Hidden year of birth column
            "headerName": "year_of_birth",
            "field": "year_of_birth",
            "hide": True,
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
                                html.H3("Cases", className="card-title"),
                                dbc.Button(
                                    "Cases Process",
                                    id="cases-process",
                                    className="card-title",
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
