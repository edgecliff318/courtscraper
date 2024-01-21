import logging
from datetime import datetime

import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc

from src.connectors.cloudtalk import fetch_call_history
from src.core.config import get_settings
from src.services import leads, messages

logger = logging.Logger(__name__)

settings = get_settings()


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


def create_graph_bar_leads_state(df: pd.DataFrame):
    df["date"] = pd.to_datetime(df["last_updated"]).dt.date
    df["source"].fillna("mo_casenet", inplace=True)
    source_rename_dict = {
        "il_cook": "IL Cook County",
        "mo_casenet": "MO Casenet",
        "mo_mshp": "MO Highway Patrol",
    }
    df["source"] = df["source"].map(source_rename_dict)
    pivot_df = df.pivot_table(
        index="date", columns="source", values="last_updated", aggfunc="count"
    )
    pivot_df = pivot_df.fillna(0)
    pivot_df["total"] = pivot_df.sum(axis=1)
    pivot_df = pivot_df.reset_index()

    columns = list(set(pivot_df.columns.to_list()) - set(["date"]))
    fig = go.Figure()
    for state in columns:
        fig.add_trace(
            go.Bar(
                x=pivot_df["date"],
                y=pivot_df[state],
                name=state,
                marker_color=settings.colors_mapping.get(state, "#FF5733"),
            )
        )

    fig.update_layout(get_base_layout(), title_text="Leads by Source")

    return dcc.Graph(figure=fig)


def create_graph_leads_status(df: pd.DataFrame):
    status_columns = [
        "not_prioritized",
        "not_contacted",
        "contacted",
        "responded",
        "not_found",
        "processing_error",
        "not_valid",
        "new",
        "processing",
        "stop",
    ]

    renamed_status_columns = {
        "not_prioritized": "Not Prioritized",
        "not_contacted": "Not Contacted",
        "contacted": "Contacted",
        "responded": "Responded",
        "not_found": "Not Found",
        "processing_error": "Processing Error",
        "not_valid": "Not Valid",
        "new": "New",
        "processing": "Processing",
        "stop": "Stop",
    }
    fig = go.Figure()
    for status in status_columns:
        fig.add_trace(
            go.Bar(
                x=[renamed_status_columns[status]],
                y=[df[df["status"] == status].shape[0]],
                name=status,
                marker_color=settings.colors_mapping[status],
            )
        )

    fig.update_layout(
        get_base_layout(),
        title_text="Leads by Status",
        xaxis_title="Status",
        yaxis_title="Leads",
        legend_title="Status",
        barmode="stack",
        coloraxis_colorbar=dict(
            thicknessmode="pixels",
            thickness=15,
            lenmode="pixels",
            len=200,
            yanchor="top",
            y=1,
            ticks="outside",
            dtick=1000,
        ),
        showlegend=False,
    )

    return dcc.Graph(figure=fig)


def create_graph_choropleth_leads_state(df: pd.DataFrame):
    leads_scraped_by_state = (
        df.fillna("MO")
        .groupby("state")
        .size()
        .reset_index(name="leads_scraped_by_state")
    )

    fig = go.Figure(
        data=go.Choropleth(
            locations=leads_scraped_by_state["state"],
            z=leads_scraped_by_state["leads_scraped_by_state"],
            locationmode="USA-states",
            colorscale="Blues",
            colorbar_title="Leads Scraped",
        )
    )

    fig.update_layout(
        geo_scope="usa",
        coloraxis_colorbar=dict(
            thicknessmode="pixels",
            thickness=15,
            lenmode="pixels",
            len=200,
            yanchor="top",
            y=1,
            ticks="outside",
            dtick=1000,
        ),
        # Deactivate Scroll Zoom
        dragmode=False,
    )

    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=True),
    )
    fig.update_yaxes(tickfont=dict(color="black"), showticklabels=True)
    fig.update_layout(
        xaxis_tickformat=" ", yaxis_tickformat=" ", yaxis_ticksuffix="  "
    )
    fig.update_layout(
        xaxis=dict(domain=[0.45, 0.95]),
        yaxis=dict(anchor="free", position=0.02, side="right"),
    )

    # Update the margin
    fig.update_layout(margin=dict(l=0, r=0, t=0.1))

    return dcc.Graph(figure=fig)


def create_graph_calls(df: pd.DataFrame):
    status_columns = ["total", "incoming", "outgoing"]
    fig = go.Figure()
    for status in status_columns:
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df[status],
                name=status,
                marker_color=settings.colors_mapping[status],
            )
        )

    fig.update_layout(
        get_base_layout(),
        title_text="Calls Overview",
    )

    return dcc.Graph(figure=fig)


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
    status_counts["total"] = sum(status_counts.values())

    return dmc.Grid(
        [
            dmc.Col(
                render_stats_card(
                    "Total Messages Sent",
                    f"{status_counts.get('sent', 0):,}",
                    "",
                ),
                md=3,
            ),
            dmc.Col(
                render_stats_card(
                    "Stop Messages Received",
                    f"{status_counts.get('stop', 0):,}",
                    "",
                ),
                md=3,
            ),
            dmc.Col(
                render_stats_card(
                    "Yes Messages Received",
                    f"{status_counts.get('yes', 0):,}",
                    "",
                ),
                md=3,
            ),
            dmc.Col(
                render_stats_card(
                    "Other Messages",
                    f"{status_counts.get('other', 0):,}",
                    "",
                ),
                md=3,
            ),
        ]
    )


def render_inbound_summary(data: pd.DataFrame):
    total_leads = len(data)

    total_leads_by_status = data.groupby("status").size().to_dict()

    return dmc.Grid(
        [
            dmc.Col(
                render_stats_card(
                    "Total leads",
                    f"{total_leads:,}",
                    "leads",
                ),
                md=4,
            ),
            dmc.Col(
                render_stats_card(
                    "New Leads",
                    f"{total_leads_by_status.get('new', 0):,}",
                    "leads",
                ),
                md=4,
            ),
            dmc.Col(
                render_stats_card(
                    "Leads Processed",
                    f"{(total_leads - total_leads_by_status.get('new', 0)):,}",
                    "leads",
                ),
                md=4,
            ),
        ]
    )


@callback(
    Output("graph-container-leads-status", "children"),
    Output("graph-container-leads-state", "children"),
    Input("stats-date-selector", "value"),
    Input("stats-refresh-button", "n_clicks"),
)
def render_scrapper_monitoring(dates, _):
    start_date, end_date = dates
    leads_list = leads.get_leads(start_date=start_date, end_date=end_date)

    if not leads_list:
        no_data_message = "No leads found for the selected period."
        return no_data_message, no_data_message

    df = pd.DataFrame([lead.model_dump() for lead in leads_list])

    graph_leads_status = create_graph_leads_status(df)
    graph_choropleth_leads_state = create_graph_choropleth_leads_state(df)
    graph_bar_leads_state = create_graph_bar_leads_state(df)

    grid_layout = dmc.Grid(
        children=[
            dmc.Col(children=graph_choropleth_leads_state, mx=1, span=5),
            dmc.Col(children=graph_bar_leads_state, mx=1, span=5),
        ],
        gutter="xl",
        justify="space-between",
    )

    return graph_leads_status, grid_layout


def process_date(date):
    try:
        creation_date = pd.to_datetime(date).tz_convert("America/Chicago")
        creation_date = creation_date.strftime("%Y-%m-%d")
    except Exception as e:
        logger.error(f"Error parsing creation_date: {e}")
        creation_date = None

    return creation_date


def fetch_messages_status(start_date, end_date):
    messages_response = messages.get_interactions_filtered(
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


@callback(
    Output("overview-inbound-summary", "children"),
    Output("overview-message-summary", "children"),
    Input("stats-date-selector", "value"),
    Input("stats-refresh-button", "n_clicks"),
)
def render_inbound_monitoring(dates, n_clicks):
    (start_date, end_date) = dates

    df_messages = fetch_messages_status(start_date, end_date)

    leads_list = leads.get_leads(start_date=start_date, end_date=end_date)
    fields = {"id", "phone", "violation", "court", "state", "status"}
    leads_list = [lead.model_dump(include=fields) for lead in leads_list]
    df_leads = pd.DataFrame(leads_list)

    inbound_summary = render_inbound_summary(df_leads)
    message_summary = render_message_summary(df_messages)

    return inbound_summary, message_summary


@callback(
    Output("graph-container-call", "children"),
    Input("stats-date-selector", "value"),
    Input("stats-refresh-button", "n_clicks"),
)
def render_call_monitoring(dates, n_clicks):
    (start_date, end_date) = dates

    start_date, end_date = [
        datetime.strptime(date, "%Y-%m-%d") for date in dates
    ]

    calls = fetch_call_history(start_date, end_date)

    df = pd.DataFrame(calls)
    if df.empty:
        no_data_message = "No calls found for the selected period."
        return dmc.Alert(
            children=no_data_message,
            color="dark",
            mb=0,
        )
    df["date"] = pd.to_datetime(df["answered_at"]).dt.date
    pivot_df = df.pivot_table(
        index="date", columns="type", values="answered_at", aggfunc="count"
    )
    pivot_df = pivot_df.fillna(0)
    pivot_df["total"] = pivot_df.sum(axis=1)
    pivot_df = pivot_df.reset_index()

    graph_calls = create_graph_calls(pivot_df)

    return graph_calls
