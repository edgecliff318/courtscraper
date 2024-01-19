import logging

import pandas as pd
from dash import Input, Output, callback, dcc

from src.core.config import get_settings
from src.services import leads
import dash_mantine_components as dmc

import plotly.graph_objects as go


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


def create_graph_leads_status(df: pd.DataFrame):
    colors_map = {
        "not_prioritized": "#FF5733",
        "not_contacted": "#FFC300",
        "contacted": "#DAF7A6",
        "responded": "#28C76F",
        "not_found": "#C70039",
        "processing_error": "#900C3F",
        "not_valid": "#581845",
        "new": "#007BFF",
        "processing": "#FFC107",
        "stop": "#FF9F43",
    }

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
    fig = go.Figure()
    for status in status_columns:
        fig.add_trace(
            go.Bar(
                x=[status],
                y=[df[df["status"] == status].shape[0]],
                name=status,
                marker_color=colors_map[status],
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
    )

    return dcc.Graph(figure=fig)


def create_graph_leads_state(df: pd.DataFrame):
    leads_scraped_by_state = (
        df.groupby("state").size().reset_index(name="leads_scraped_by_state")
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
        title_text="Leads Scraped by State",
        geo_scope="usa",
        margin=dict(l=0, r=0, t=0, b=0),
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
    )

    return dcc.Graph(figure=fig)


class LeadPipeline:
    # Leads Scraped Today
    def leads_scraped_today(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Process the data.
        add a column with the number of leads scraped today
        """
        data["leads_scraped_today"] = data[
            data["last_updated"].dt.date == pd.Timestamp.today().date()
        ].count()["id"]

        return data

    # Leads Scraped by State
    def leads_scraped_by_state(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Process the data.
        add a column with the number of leads scraped today
        """
        states_count = data.groupby("state").count()["id"].to_dict()
        data["leads_scraped_by_state"] = data.state.map(states_count)

        return data

    # Leads by status
    def leads_by_status(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Process the data.
        add a column with the number of leads scraped today
        """
        status_count = data.groupby("status").count()["id"].to_dict()
        data["leads_by_status"] = data.status.map(status_count)

        return data

    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Process the data.
        """
        return data.pipe(self.leads_scraped_today)


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


@callback(
    Output("graph-container-leads-status", "children"),
    Output("graph-container-leads-state", "children"),
    Input("monitoring-date-selector", "value"),
    Input("scrapper-selector", "value"),
    Input("scrapper-refresh-button", "n_clicks"),
)
def render_scrapper_monitoring(dates, scrapper, n_clicks):
    (start_date, end_date) = dates
    # ctx = dash.callback_context
    # trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    leads_list = leads.get_leads(
        start_date=start_date,
        end_date=end_date,
    )
    df = pd.DataFrame([lead.model_dump() for lead in leads_list])
    return create_graph_leads_status(df), create_graph_leads_state(df)
