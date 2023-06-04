import logging

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback, html

from src.commands import leads as leads_commands
from src.components.toast import build_toast
from src.core.config import get_settings
from src.services import messages as messages_service

logger = logging.Logger(__name__)

settings = get_settings()


@callback(
    Output("message-monitoring", "children"),
    Input("monitoring-date-selector", "start_date"),
    Input("monitoring-date-selector", "end_date"),
    Input("monitoring-status-selector", "value"),
)
def render_status_msg(start_date, end_date, direction):
    # TODO: Read from DB from firebase and display in the grid
    # NOTE: This is a dummy data
    grid = "Empty"
    if direction == "all":
        direction = None

    interactions_list = messages_service.get_interactions_filtered(
        start_date=start_date,
        end_date=end_date,
        direction=direction,
    )
    df = pd.DataFrame(
        [interaction.dict() for interaction in interactions_list]
    )
    cols = [
        "case_id",
        "creation_date",
        "phone",
        "direction",
        "status",
        "id",
        "message",
    ]
    df = df[cols]

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

    # Make the creation date tz naive
    df["creation_date"] = pd.to_datetime(df["creation_date"], utc=True)

    # Transform to local timezone of Central Time
    df["creation_date"] = df["creation_date"].dt.tz_convert("US/Central")

    df.sort_values(by=["creation_date"], inplace=True, ascending=False)
    df["creation_date"] = df["creation_date"].dt.strftime(
        "%m/%d/%Y - %H:%M:%S"
    )
    df = df.set_index("case_id")
    df = df.rename(
        columns={
            "creation_date": "Sending At",
            "phone": "Phone",
            "direction": "Direction",
            "status": "Status",
            "id": "SID",
            "message": "Message",
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
                for col in ["Phone"]
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
                for col in ["Direction", "Status", "SID", "Message"]
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


@callback(
    Output("monitoring-status", "children"),
    Input("monitoring-refresh-button", "n_clicks"),
    Input("monitoring-date-selector", "start_date"),
    Input("monitoring-date-selector", "end_date"),
)
def refresh_messages(n_clicks, start_date, end_date):
    ctx = dash.callback_context
    button = ctx.triggered[0]["prop_id"].split(".")[0]
    if button == "monitoring-refresh-button":
        try:
            leads_commands.sync_twilio()
            return build_toast(
                "Messages refreshed successfully",
                "Messages refreshed",
            )
        except Exception as e:
            logger.error(e)
            return build_toast(
                f"Messages refreshed failed with {e}",
                "Messages refreshed",
            )
