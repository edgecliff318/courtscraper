import logging

import dash.html as html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, callback, html

from src.components.cards import render_stats_card
from src.core.config import get_settings
from src.core.format import humanize_phone
from src.services import leads

logger = logging.Logger(__name__)

settings = get_settings()


def render_inbound_summary(data: dict):
    return dmc.Grid(
        [
            dmc.GridCol(
                render_stats_card(
                    "New Leads",
                    f"{data.get('leads_added_today'):,}",
                    "leads",
                ),
                span={"base": 12, "md": 4},
            ),
            dmc.GridCol(
                render_stats_card(
                    "Not Contacted Leads",
                    f"{data.get('not_contacted'):,}",
                    "leads",
                ),
                span={"base": 12, "md": 4},
            ),
            dmc.GridCol(
                render_stats_card(
                    "Converted Leads",
                    f"{data.get('leads_converted'):,}",
                    "leads",
                ),
                span={"base": 12, "md": 4},
            ),
        ]
    )


@callback(
    Output("leads-data", "children"),
    Input("court-selector", "value"),
    Input("date-selector", "value"),
    Input("lead-status-selector", "value"),
)
def render_leads(court_code_list, dates, status):
    (start_date, end_date) = dates
    grid = "Empty"
    if status == "all":
        status = None
    leads_list = leads.get_leads(court_code_list, start_date, end_date, status)
    df = pd.DataFrame([lead.model_dump() for lead in leads_list])
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
            "state",
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

    def transform_phones(phones):
        if isinstance(phones, dict):
            return ", ".join(
                [humanize_phone(v.get("phone")) for k, v in phones.items()]
            )
        else:
            return phones

    def transform_emails(emails):
        if isinstance(emails, dict):
            return ", ".join(
                [v.get("address") for k, v in emails.items() if k == "0"]
            )
        else:
            return emails

    df["phone"] = df["phone"].map(transform_phones)
    df["email"] = df["email"].map(transform_emails)

    df["case_index"] = df.index

    total_leads = len(df)
    total_phones = df.phone.map(
        lambda x: len(x.split(",")) if x is not None else 0
    ).sum()

    df = df.rename(
        columns={
            "state": "State",
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
            "headerName": "State",
            "field": "State",
            "editable": False,
            "filter": "agTextColumnFilter",
            "sortable": True,
            "resizable": True,
            "flex": 1,
        },
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
        id="outbound-data-grid",
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
                                dmc.Group(
                                    [
                                        dmc.Text(
                                            f"{total_leads} Leads",
                                            size="sm",
                                            c="gray",
                                        ),
                                        dmc.Text(
                                            f"{total_phones} Phones",
                                            size="sm",
                                            c="gray",
                                        ),
                                        dmc.Button(
                                            "Cases Process",
                                            id="outbound-response-many",
                                            color="dark",
                                            # className="card-title",
                                        ),
                                    ]
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
