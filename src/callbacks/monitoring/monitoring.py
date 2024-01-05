import logging

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from dash import Input, Output, callback, html, dcc
import plotly.graph_objects as go

from src.commands import leads as leads_commands
from src.components.toast import build_toast
from src.core.config import get_settings
from src.services import messages as messages_service

logger = logging.Logger(__name__)
settings = get_settings()


@callback(Output("switch-settings-txt", "children"), Input("switch-automated_message", "checked"))
def settings(checked):
    return f"Automated Messaging {'Run' if checked else 'Stop'} "

def get_data_status_sms():
    date_range = pd.date_range(start="2023-01-01", end="2023-01-31", freq="D")
    data = {
        "date": date_range,
        "stop": np.random.randint(1, 15, size=len(date_range)),
        "yes": np.random.randint(1, 15, size=len(date_range)),
        "pending": np.random.randint(1, 15, size=len(date_range)),
        "error": np.random.randint(1, 15, size=len(date_range)),
    }

    df = pd.DataFrame(data)
    return df


def get_data_most_recent_error():
    error_labels = [f"Error {i+1}" for i in range(15)]
    error_counts = np.random.randint(1, 50, size=15)

    df = pd.DataFrame({"Error": error_labels, "Count": error_counts})
    df = df.sort_values(by="Count", ascending=True)
    return df


def create_graph_status_sms():
    df = get_data_status_sms()
    colors_map = {
        "pending": "grey",
        "stop": "#FF9F43",
        "yes": "#28C76F",
        "error": "#F8795D",
    }
    fig = go.Figure()
    for col in ["pending", "stop", "yes", "error"]:
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df[col],
                name=col.capitalize(),
                marker_color=colors_map[col],
            )
        )

    fig.update_layout(
        title="Response Overview",
        xaxis=dict(
            title="Date",
            tickfont_size=14,
            showline=True,
            showgrid=True,
            gridcolor="LightGrey",
            linecolor="LightGrey",
        ),
        yaxis=dict(
            title="Number of Responses",
            titlefont_size=16,
            tickfont_size=14,
            showline=True,
            showgrid=True,
            gridcolor="LightGrey",
            linecolor="LightGrey",
        ),
        barmode="stack",
        paper_bgcolor="rgba(255, 255, 255, 0)",
        plot_bgcolor="rgba(255, 255, 255, 0)",
    )

    return dcc.Graph(figure=fig)


def create_graph_most_recent_error():
    df = get_data_most_recent_error()
    max_count = df["Count"].max()
    color_scale = [
        "#FFEDA0",
        "#FED976",
        "#FEB24C",
        "#FD8D3C",
        "#FC4E2A",
        "#E31A1C",
        "#BD0026",
        "#800026",
    ]

    df["color"] = df["Count"].apply(
        lambda x: color_scale[int((len(color_scale) - 1) * x / max_count)]
    )

    y_values = list(range(1, len(df["Error"]) + 1))

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            y=y_values,
            x=df["Count"],
            name="Error",
            marker_color=df["color"],
            text=df["Error"],
            textposition="inside",
            orientation="h",
            width=0.8,
        )
    )

    fig.update_layout(
        title="Most Recent Errors",
        yaxis=dict(title="Error Types", tickvals=y_values, tickfont_size=14),
        xaxis=dict(
            title="Count",
            titlefont_size=16,
            tickfont_size=14,
            showline=True,
            showgrid=True,
            gridcolor="LightGrey",
            linecolor="LightGrey",
        ),
        paper_bgcolor="rgba(255, 255, 255, 0)",
        plot_bgcolor="rgba(255, 255, 255, 0)",
    )

    return dcc.Graph(figure=fig)


@callback(
    Output("graph-container-status-sms", "children"),
    Input("monitoring-date-selector", "value"),
    Input("monitoring-status-selector", "value"),
)
def graph_status_sms(value, direction):
    return create_graph_status_sms()


@callback(
    Output("graph-container-most-recent-error", "children"),
    Input("monitoring-date-selector", "value"),
    Input("monitoring-status-selector", "value"),
)
def graph_most_recent_error(value, direction):
    return create_graph_most_recent_error()


@callback(
    Output("message-monitoring", "children"),
    Input("monitoring-date-selector", "value"),
    Input("monitoring-status-selector", "value"),
)
def render_status_msg(dates, direction):
    (start_date, end_date) = dates
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
    df = pd.DataFrame([interaction.model_dump() for interaction in interactions_list])
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
    df["creation_date"] = df["creation_date"].dt.strftime("%m/%d/%Y - %H:%M:%S")
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
    Input("monitoring-date-selector", "value"),
)
def refresh_messages(n_clicks, dates):
    (start_date, end_date) = dates
    ctx = dash.callback_context
    button = ctx.triggered[0]["prop_id"].split(".")[0]
    if button == "monitoring-refresh-button":
        try:
            leads_commands.sync_twilio(from_date=start_date, to_date=end_date)
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
