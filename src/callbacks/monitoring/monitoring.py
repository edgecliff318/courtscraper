import logging
import re

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, ctx, dcc, html
from dash_iconify import DashIconify

from src.commands import leads as leads_commands
from src.components.toast import build_toast
from src.db import db
from src.services import messages as messages_service
from src.services.settings import get_settings as db_settings

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


logger = logging.Logger(__name__)


def extract_case_id(text):
    pattern = r"\[(\d+)\]"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def process_date(date):
    try:
        creation_date = pd.to_datetime(date).tz_convert("America/Chicago")
        creation_date = creation_date.strftime("%Y-%m-%d")
    except Exception as e:
        logger.error(f"Error parsing creation_date: {e}")
        creation_date = None

    return creation_date


def fetch_messages_status(start_date, end_date):
    messages_response = messages_service.get_interactions_filtered(
        start_date=start_date,
        end_date=end_date,
    )

    def map_status(message):
        if message.direction == "outbound":
            return "sent"
        if message.message is not None:
            if "stop" in message.message.lower():
                return "stop"
            elif "yes" in message.message.lower():
                return "yes"
            else:
                return "other"
        else:
            return "other"

    messages_list = [
        {
            "id": message.id,
            "case_id": message.case_id,
            "direction": message.direction,
            "creation_date": message.creation_date,
            "status": map_status(message),
            "message_status": message.status,
        }
        for message in messages_response
    ]

    df = pd.DataFrame(messages_list)

    df["date"] = df["creation_date"].apply(process_date)
    return df


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
                    fw=600,
                    c="dark",
                ),
                dmc.Group(
                    [
                        dmc.Title(
                            kpi_value_formatted,
                            order=1,
                            c="indigo",
                        ),
                        dmc.Text(
                            kpi_unit,
                            fw=500,
                            c="dark",
                            mb=4,
                        ),
                    ],
                    align="flex-end",
                ),
            ],
            gap="sm",
            align="center",
        ),
    )


def render_message_summary(df: pd.DataFrame):
    status_counts = df.status.value_counts().to_dict()
    status_counts["total"] = sum(status_counts.values())

    return dmc.Grid(
        [
            dmc.GridCol(
                render_stats_card(
                    "Total Messages Sent",
                    f"{status_counts.get('sent', 0):,}",
                    "",
                ),
                span={"base": 12, "md": 3},
            ),
            dmc.GridCol(
                render_stats_card(
                    "Stop Messages Received",
                    f"{status_counts.get('stop', 0):,}",
                    "",
                ),
                span={"base": 12, "md": 3},
            ),
            dmc.GridCol(
                render_stats_card(
                    "Yes Messages Received",
                    f"{status_counts.get('yes', 0):,}",
                    "",
                ),
                span={"base": 12, "md": 3},
            ),
            dmc.GridCol(
                render_stats_card(
                    "Other Messages",
                    f"{status_counts.get('other', 0):,}",
                    "",
                ),
                span={"base": 12, "md": 3},
            ),
        ]
    )


def create_graph_status_sms(df: pd.DataFrame) -> dcc.Graph:
    colors_map = {
        "other": "#6610F2",
        "stop": "#FF9F43",
        "yes": "#28C76F",
        "sent": "#053342",
    }

    fig = go.Figure()
    for col in ["stop", "yes", "other", "sent"]:
        if col in df.columns:
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


def create_graph_most_recent_error(start_date, end_date):
    twilio_messages = leads_commands.get_twilio_messages(
        from_date=start_date, to_date=end_date
    )

    df = pd.DataFrame(
        [
            {
                # Twilio API
                "account_sid": message.account_sid,
                "date_created": message.date_created,
                "date_updated": message.date_updated,
                "date_sent": message.date_sent,
                "direction": message.direction,
                "error_code": message.error_code,
                "error_message": message.error_message,
                "price": message.price,
                "status": message.status,
                "from_": message.from_,
                "to": message.to,
                "body": message.body,
            }
            for message in twilio_messages
        ]
    )

    df["error_message"].fillna("No Error", inplace=True)

    df["date_created"] = pd.to_datetime(df["date_created"])
    df["date_updated"] = pd.to_datetime(df["date_updated"])
    df["date_sent"] = pd.to_datetime(df["date_sent"])

    # Group by error code
    error_counts = df.groupby("error_message").size()
    error_counts = error_counts.reset_index()
    error_counts.columns = ["Error", "Count"]
    error_counts = error_counts.sort_values(by="Count", ascending=True)
    max_count = error_counts["Count"].max()

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

    error_counts["color"] = error_counts["Count"].apply(
        lambda x: color_scale[int((len(color_scale) - 1) * x / max_count)]
    )

    # Analysis DF
    df_analysis = df[df["direction"] == "outbound-api"]

    if df_analysis.empty:
        return dmc.Text("No data to display")

    df_grouped = df_analysis.pivot_table(
        index="body",
        columns="error_message",
        values="account_sid",
        aggfunc="count",
    )

    # Add a tag if "Carrier violation" is higher than 10% of the total for each row

    if "Carrier violation" not in df_grouped.columns:
        df_grouped["Carrier violation"] = 0

    df_grouped["Carrier violation"] = df_grouped["Carrier violation"].fillna(0)
    df_grouped["Total"] = df_grouped.sum(axis=1)
    df_grouped["Carrier violation %"] = (
        df_grouped["Carrier violation"] / df_grouped["Total"]
    ).fillna(0)

    df_grouped["Focus"] = (
        df_grouped["Carrier violation"] > 0.1 * df_grouped["Total"]
    )
    df_grouped = df_grouped.reset_index()

    def render_message(row):
        content = dmc.Card(
            dmc.Stack(
                [
                    dmc.Group(
                        [
                            dmc.Text(
                                "Statistics",
                                size="sm",
                                fw=600,
                                c="dark",
                            ),
                            dmc.Text(
                                f"Total: {row.Total:.0f}", size="sm", c="dark"
                            ),
                            dmc.Text(
                                f"Carrier violation: {row['Carrier violation']:.0f}",
                                size="sm",
                                c="dark",
                            ),
                            dmc.Text(
                                f"Carrier violation %: {row['Carrier violation %']:.2%}",
                                size="sm",
                                c="dark",
                            ),
                            dmc.ActionIcon(
                                DashIconify(
                                    icon=(
                                        "ic:round-error"
                                        if row.Focus
                                        else "ic:round-done"
                                    ),
                                    width=20,
                                ),
                                id="button",
                                radius="md",
                                size="lg",
                                mr=17,
                                variant="light",
                                color="red" if row.Focus else "green",
                            ),
                        ],
                        justify="left",
                    ),
                    dmc.Text(row.body, size="xs"),
                ]
            ),
            withBorder=True,
            shadow="sm",
            radius="md",
        )
        return content

    # Table with the
    errors_by_message = dmc.Stack(
        [
            dmc.Title("Errors by message", order=2, fw=600, c="dark"),
            dmc.Stack(
                [render_message(row) for _, row in df_grouped.iterrows()]
            ),
        ]
    )

    df_grouped_phone_nbs = df_analysis.pivot_table(
        index="from_",
        columns="error_message",
        values="account_sid",
        aggfunc="count",
    )

    df_grouped_phone_nbs.fillna(0, inplace=True)
    df_grouped_phone_nbs["Total"] = df_grouped_phone_nbs.sum(axis=1)

    error_columns = [
        col
        for col in df_grouped_phone_nbs.columns
        if col != "Total" and col != "No Error"
    ]

    if "Carrier violation" not in df_grouped_phone_nbs.columns:
        df_grouped_phone_nbs["Carrier violation"] = 0

    for col in df_grouped_phone_nbs.columns:
        if col not in ["Total"]:
            df_grouped_phone_nbs[f"{col} %"] = (
                df_grouped_phone_nbs[col] / df_grouped_phone_nbs["Total"]
            )

    df_grouped_phone_nbs["Focus"] = (
        df_grouped_phone_nbs["Carrier violation"]
        > 0.1 * df_grouped_phone_nbs["Total"]
    )

    df_grouped_phone_nbs = df_grouped_phone_nbs.reset_index()

    def render_phone_number(row):
        content = dmc.Card(
            dmc.Group(
                [
                    dmc.Text(
                        f"Statistics for {row.from_}",
                        size="sm",
                        fw=600,
                        c="dark",
                    ),
                    dmc.Text(f"Total: {row.Total:.0f}", size="sm", c="dark"),
                    dmc.Text(
                        f"Carrier violation: {row['Carrier violation']:.0f}",
                        size="sm",
                        c="dark",
                    ),
                    dmc.Text(
                        f"Carrier violation %: {row['Carrier violation %']:.2%}",
                        size="sm",
                        c="dark",
                    ),
                    dmc.ActionIcon(
                        DashIconify(
                            icon=(
                                "ic:round-error"
                                if row.Focus
                                else "ic:round-done"
                            ),
                            width=20,
                        ),
                        id="button",
                        radius="md",
                        size="lg",
                        mr=17,
                        variant="light",
                        color="red" if row.Focus else "green",
                    ),
                ],
                justify="left",
            ),
            withBorder=True,
            shadow="sm",
            radius="md",
        )
        return content

    # Global Results
    df_grouped_global = df_analysis.groupby("error_message").size()
    df_grouped_global = df_grouped_global.reset_index()
    df_grouped_global.columns = ["Error", "Count"]
    df_grouped_global = df_grouped_global.sort_values(
        by="Count", ascending=True
    )

    total = df_grouped_global["Count"].sum()

    if "Carrier violation" not in df_grouped_global["Error"].values:
        carrier_violation = 0
    else:
        carrier_violation = df_grouped_global[
            df_grouped_global["Error"] == "Carrier violation"
        ]["Count"].values[0]

    focus = carrier_violation > 0.1 * total

    global_results = dmc.Stack(
        [
            dmc.Title("Global Results", order=2, fw=600, c="dark"),
            dmc.Group(
                [
                    dmc.Text(
                        "Statistics",
                        size="sm",
                        fw=600,
                        c="dark",
                    ),
                    dmc.Text(f"Total: {total:.0f}", size="sm", c="dark"),
                    dmc.Text(
                        f"Carrier violation: {carrier_violation:.0f}",
                        size="sm",
                        c="dark",
                    ),
                    dmc.Text(
                        f"Carrier violation %: {carrier_violation / total:.2%}",
                        size="sm",
                        c="dark",
                    ),
                    dmc.ActionIcon(
                        DashIconify(
                            icon=(
                                "ic:round-error" if focus else "ic:round-done"
                            ),
                            width=20,
                        ),
                        id="button",
                        radius="md",
                        size="lg",
                        mr=17,
                        variant="light",
                        color="red" if focus else "green",
                    ),
                ],
                justify="left",
            ),
        ],
    )

    errors_by_phone = dmc.Stack(
        [
            dmc.Title("Errors by phone number", order=2, fw=600, c="dark"),
            dmc.Stack(
                [
                    render_phone_number(row)
                    for _, row in df_grouped_phone_nbs.iterrows()
                ]
            ),
        ]
    )

    return dmc.Stack([global_results, errors_by_phone, errors_by_message])


@callback(
    Output("graph-container-status-sms", "children"),
    Output("messages-summary", "children"),
    Input("monitoring-date-selector", "value"),
    Input("monitoring-status-selector", "value"),
)
def graph_status_sms(dates, direction):
    (start_date, end_date) = dates
    df = fetch_messages_status(start_date, end_date)
    pivot_df = df.pivot_table(
        index="date", columns="status", values="case_id", aggfunc="count"
    )
    pivot_df = pivot_df.fillna(0)
    columns = ["stop", "yes", "other", "sent"]

    for col in columns:
        if col not in pivot_df.columns:
            pivot_df[col] = 0

    pivot_df = pivot_df.reset_index()
    pivot_df = pivot_df[
        [
            c
            for c in pivot_df.columns
            if c in ["date", "stop", "yes", "other", "sent"]
        ]
    ]

    return [create_graph_status_sms(pivot_df), render_message_summary(df)]


@callback(
    Output("graph-container-most-recent-error", "children"),
    Input("monitoring-date-selector", "value"),
    Input("monitoring-status-selector", "value"),
)
def graph_most_recent_error(dates, direction):
    (start_date, end_date) = dates

    output = create_graph_most_recent_error(start_date, end_date)

    return output


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
    Output("monitoring-data", "data"),
    Input("monitoring-date-selector", "value"),
    Input("monitoring-status-selector", "value"),
    prevent_initial_call=False,
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
    df = pd.DataFrame(
        [interaction.model_dump() for interaction in interactions_list]
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
    df["case_index"] = df["Case ID"]
    df["Case ID"] = df["Case ID"].map(lambda x: f"[{x}](/case/{x})")

    number_of_leads = df["Case ID"].nunique()

    column_defs = [
        {
            # Hidden case id column
            "headerName": "case_index",
            "field": "case_index",
            "hide": True,
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
                for col in ["Direction", "Message"]
            ],
        },
    ]

    grid = dag.AgGrid(
        id="monitoring-data-grid",
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
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.H3(
                            "SMS Monitoring of Leads",
                            className="card-title m-1",
                        ),
                        dmc.Group(
                            [
                                dmc.Text(
                                    f"Number of leads: {number_of_leads}"
                                ),
                                dmc.Button(
                                    "Unselect All",
                                    id="conversation-response-unselect-all",
                                    color="dark",
                                    size="sm",
                                    className="m-2",
                                ),
                                dmc.Button(
                                    "Show Conversation",
                                    id="conversation-response-many",
                                    color="dark",
                                    size="sm",
                                    className="m-2",
                                ),
                                dmc.Button(
                                    "Bulk response",
                                    id="monitoring-response-many",
                                    color="dark",
                                    size="sm",
                                    className="m-2",
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
    ], df.to_dict("records")


@callback(
    Output("monitoring-status", "children"),
    Input("monitoring-refresh-button", "n_clicks"),
    Input("monitoring-date-selector", "value"),
    prevent_initial_call=True,
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


def conversation(df_conversation):
    container = html.Div(
        [
            dmc.Container(
                [
                    # Message from the user
                    dmc.Paper(
                        children="This is a user message.",
                        withBorder=True,
                        p="md",
                        shadow="sm",
                        style={
                            "backgroundColor": "#e0f7fa",
                            "textAlign": "left",
                            "marginBottom": "10px",
                        },
                    ),
                    dmc.Paper(
                        children="This is a response from the system.",
                        withBorder=True,
                        p="md",
                        shadow="sm",
                        style={
                            "backgroundColor": "#ffe0b2",
                            "textAlign": "right",
                            "marginBottom": "10px",
                        },
                    ),
                ],
                style={"maxWidth": 500},
            )
        ]
    )

    return dmc.Stack(
        [
            container,
            dmc.TextInput(
                styles={
                    "input": {
                        "fontSize": 15,
                        "boxShadow": "rgba(99, 99, 99, 0.2) 0px 2px 8px 0px",
                        "border": "none",
                    },
                },
                id="message-response-input",
                placeholder="What do you want to know about your business?",
                radius="lg",
                size="lg",
                w="80%",
                m="auto",
                rightSection=dmc.ActionIcon(
                    DashIconify(icon="ic:round-send", width=20),
                    id="button",
                    radius="md",
                    size="lg",
                    mr=17,
                ),
            ),
        ]
    )


@callback(
    Output("modal-conversation", "opened"),
    Output("modal-conversation-content", "children"),
    Input("monitoring-data-grid", "selectedRows"),
    State("monitoring-data", "data"),
    Input("show-conversation", "n_clicks"),
    Input("message-monitoring", "children"),
    Input("monitoring-date-selector", "value"),
    State("monitoring-memory", "data"),
    prevent_initial_call=False,
)
def open_modal_conversation(selection, data, *args, **kwargs):
    if selection and ctx.triggered_id == "show-conversation":
        df = pd.DataFrame(selection)
        df_filter = df[
            [
                "Phone",
                "Direction",
                "Message",
            ]
        ]
        if df_filter.empty:
            return False, dash.no_update

        case_id = extract_case_id(df["Case ID"].iloc[0])

        messages = messages_service.get_interactions(case_id=case_id)
        df_conversation = pd.DataFrame(
            [message.model_dump() for message in messages]
        )
        df_conversation["creation_date"] = pd.to_datetime(
            df_conversation["creation_date"], utc=True
        )
        df_conversation.sort_values(
            by=["creation_date"], inplace=True, ascending=True
        )
        df_conversation["creation_date"] = df_conversation[
            "creation_date"
        ].dt.tz_convert("US/Central")
        df_conversation = df_conversation[
            ["direction", "message", "creation_date"]
        ]
        return True, conversation(df_conversation)

    return dash.no_update, dash.no_update
