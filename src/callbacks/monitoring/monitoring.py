import logging

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from dash import Input, Output, callback, html, dcc
import dash_mantine_components as dmc
import plotly.graph_objects as go

from src.commands import leads as leads_commands
from src.components.toast import build_toast
from src.services import messages as messages_service
from src.services.settings import get_settings as db_settings
from src.db import db




logger = logging.Logger(__name__)

def process_date(date):
    try:
        creation_date = pd.to_datetime(date, unit="ms")
    except Exception as e:
        logger.error(f"Error parsing creation_date: {e}")
        creation_date = pd.to_datetime(date)

    # UTC to Central time
    creation_date = creation_date.tz_convert("America/Chicago")
    creation_date = creation_date.strftime("%Y-%m-%d")


    return creation_date
def fetch_messages_status():  #start_date, end_date):
     # Fields selection
    lead_fields = {
        "id",
        "case_id",
        "status",
    }
    message_fields = {
        "id",
        "case_id",
        "direction",
        "status",
        "creation_date",
    }
    # messages_response = messages.get_interactions_filtered(
    #     start_date="2023-09-25",
    #     end_date="2024-09-26",
    # )
    # messages_list = []
    # for message in messages_response:
    #     message_data =message.model_dump(include=message_fields)
    #     lead = leads.get_single_lead(message_data.get("case_id"))
    #     if lead:
    #         lead = lead.model_dump(include=lead_fields)
    #         message_data['status'] = lead.get('status')
    #     messages_list.append(message_data)
    # df = pd.DataFrame(messages_list)
    df = pd.read_csv("leads.csv")
    def map_status(status):
        if status in ['stop', 'yes']:
            return status
        else:
            return 'other'
    df["date"] = df["creation_date"].apply(process_date)
    df["status"] = df["status"].map(map_status)
    return df

   


        
    



COLORS = {
    "blue": "#2B8FB3",
    "indigo": "#6610F2",
    "purple": "#053342",
    "pink": "#D63384",
    "red": "#F8795D",
    "orange": "#F8795D",
    "yellow": "#FF9F43",
    "green": "#28C76F",
    "teal": "#20C997",
}

def get_base_layout():
    margin_top = 100
    margin = go.layout.Margin(l=40, r=40, b=40, t=margin_top, pad=0)
    font = dict(size=12, color="#6E6B7B")
    bgcolor = "rgba(255, 255, 255, 0)"
    legend = dict(
        orientation="h",
        x=1,
        y=1.02,
        xanchor="right",
        yanchor="bottom",
        font=font,
        bgcolor=bgcolor,
        bordercolor=bgcolor,
        borderwidth=0,
    )
    layout = go.Layout(
        autosize=True,
        plot_bgcolor=bgcolor,
        paper_bgcolor=bgcolor,
        margin=margin,
        font=font,
        legend=legend,
    )
    return layout
def render_stats_card(kpi_name, kpi_value_formatted, kpi_unit):
    return dmc.Card(
        children=dmc.Stack(
            [
                dmc.Text(
                    kpi_name,
                    size="md",
                    weight=600,
                    color="dark",
                ),
                dmc.Group(
                    [
                        dmc.Title(
                            kpi_value_formatted,
                            order=1,
                            color="indigo",
                        ),
                        dmc.Text(
                            kpi_unit,
                            weight=500,
                            color="dark",
                            mb=4,
                        ),
                    ],
                    align="flex-end",
                ),
            ],
            spacing="sm",
            align="center",
        ),
    )


def render_message_summary(df: pd.DataFrame):    
    status_counts = df.status.value_counts().to_dict()
    status_counts['total'] = sum(status_counts.values())

    return dmc.Grid(
        [
            dmc.Col(
                render_stats_card(
                    "Total message send",
                    f"{status_counts.get('total', 0):,}",
                    "",
                ),
                md=3,
            ),
            dmc.Col(
                render_stats_card(
                    "Total message stop",
                    f"{status_counts.get('stop', 0):,}",
                    "",
                ),
                md=3,
            ),
            dmc.Col(
                render_stats_card(
                    "Total message yes",
                    f"{status_counts.get('yes', 0):,}",
                    "",
                ),
                md=3,
            ),
             dmc.Col(
                render_stats_card(
                    "Total message other",
                    f"{status_counts.get('other', 0):,}",
                    "",
                ),
                md=3,
            ),
        ]
    )
    




def create_graph_status_sms(df: pd.DataFrame)-> dcc.Graph:
    colors_map = {
        "other": "grey",
        "stop": "#FF9F43",
        "yes": "#28C76F",
        "total": "#F8795D",
    }
    
    fig = go.Figure()
    for col in ['stop', 'yes', 'other' ,'total']:
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df[col],
                name=col.capitalize(),
                marker_color=colors_map[col],
            )
        )

   
    fig.update_layout(
        get_base_layout(),
        title="Response Overview",
    )
    return dcc.Graph(figure=fig)


def create_graph_most_recent_error():
    error_labels = [f"Error {i+1}" for i in range(15)]
    error_counts = np.random.randint(1, 50, size=15)
    df = pd.DataFrame({"Error": error_labels, "Count": error_counts})
    df = df.sort_values(by="Count", ascending=True)
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
        get_base_layout(),
        title="Most Recent Error",
        xaxis_title="Count",
        yaxis_title="Error",
    )
    return dcc.Graph(figure=fig)


@callback(
    Output("graph-container-status-sms", "children"),
    Output("messages-summary", "children"),
    Input("monitoring-date-selector", "value"),
    Input("monitoring-status-selector", "value"),
)
def graph_status_sms(value, direction):
    
    df = fetch_messages_status()
    pivot_df = df.pivot_table(index='date', columns='status', values='case_id', aggfunc='count')
    pivot_df = pivot_df.fillna(0)
    pivot_df['total'] = pivot_df.sum(axis=1)
    pivot_df = pivot_df.reset_index()
    pivot_df = pivot_df[['date', 'stop', 'yes', 'other' ,'total']]
    
    
    
    return [create_graph_status_sms(pivot_df),
            render_message_summary(df)
    ]


@callback(
    Output("graph-container-most-recent-error", "children"),
    Input("monitoring-date-selector", "value"),
    Input("monitoring-status-selector", "value"),
)
def graph_most_recent_error(value, direction):
    return create_graph_most_recent_error()



@callback(
    Output("switch-automated_message", "checked"),
    Output("switch-settings-txt", "children"),
    Input("switch-automated_message", "checked"),
)
def settings(checked):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "switch-automated_message":
        db.collection("settings").document("main").update(
            {"automated_messaging": checked}
        )
    settings_sms = db_settings("main")
    return (
        settings_sms.automated_messaging,
        f"Automated Messaging {'Run' if settings_sms.automated_messaging else 'Stop'} ",
    )
    
    

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
                                        dmc.Button(
                                            "Remove ",
                                            id="cases-process",
                                            color="dark",
                                            size="sm",
                                            className="m-1",
                                        ),
                                        dmc.Button(
                                            "Resend",
                                            id="cases-process",
                                            color="dark",
                                            size="sm",
                                            className="m-1",
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
