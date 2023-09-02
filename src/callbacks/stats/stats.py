import logging

import dash
import dash.html as html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback

from src.components import tables
from src.components.figures import empty_figure
from src.core.config import get_settings
from src.services import courts, leads, messages

logger = logging.Logger(__name__)

settings = get_settings()


@callback(
    Output("overview", "children"),
    Output("leads-by-county", "figure"),
    Output("leads-by-status", "figure"),
    Output("interactions-by-date", "figure"),
    Output("stats-for-each-county", "children"),
    Input("leads-button", "n_clicks"),
    Input("court-selector", "value"),
    Input("date-selector", "value"),
    Input("lead-status-selector", "value"),
)
def render_leads(search, court_code_list, dates, status):
    (start_date, end_date) = dates
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == "leads-button":
        if status == "all":
            status = None
        leads_list = leads.get_leads(
            court_code_list, start_date, end_date, status
        )
        data = pd.DataFrame([lead.model_dump() for lead in leads_list])

        if data.empty:
            return (
                [],
                empty_figure(),
                empty_figure(),
                empty_figure(),
                [],
            )

        courts_list = courts.get_courts()
        # Show in a graph the len of the data by county and by date
        courts_dict = {court.code: court.name for court in courts_list}
        data["court_name"] = data.court_code.map(courts_dict)
        leads_by_country = px.bar(
            data.groupby("court_name").case_id.count(), title="Leads by county"
        )
        # Improve the style of the graph
        leads_by_country.update_layout(
            xaxis_title="County",
            yaxis_title="Number of leads",
            font=dict(size=18, color="#7f7f7f"),
        )

        # Leads by status
        leads_by_status_df = data.groupby("status").case_id.count()
        # Remove the status not_contacted from the index
        leads_by_status_df = leads_by_status_df.loc[
            [i for i in leads_by_status_df.index if i != "not_contacted"]
        ]

        leads_by_status = px.pie(
            leads_by_status_df,
            title="Leads by status",
            values="case_id",
            names=leads_by_status_df.index,
        )

        interactions = messages.get_interactions()
        interactions_df = pd.DataFrame(
            [interaction.model_dump() for interaction in interactions]
        )

        data = data.join(
            interactions_df.groupby("case_id").message.count(),
            on="case_id",
            how="left",
        )

        data["interactions_counts"] = data.message.fillna(0)

        # Plot the bars of the interactions by date from the total amount
        # of cases
        interactions = data.groupby("case_date").agg(
            {"interactions_counts": "sum", "case_id": "count"}
        )
        interactions["interactions_per_case"] = (
            interactions.interactions_counts / interactions.case_id
        )
        interactions_by_date = px.bar(
            data.groupby("case_date").interactions_counts.sum(),
            title="Interactions by date",
            color_discrete_sequence=["red"],
        )
        # Add the total number of cases by date in red
        interactions_by_date.add_trace(
            px.bar(
                data.groupby("case_date").case_id.count(),
                title="Cases by date",
            ).data[0]
        )

        cases_with_phone_nb = (
            data.phone.map(lambda x: 1 if "no" not in x.lower() else 0).sum()
            / data.case_id.count()
        )

        total_cases_with_phone_nb = f"{cases_with_phone_nb*100:.2f}%"

        overview = dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("Total cases"),
                                html.Hr(className="my-2"),
                                html.H1(
                                    f"{data.case_id.count():.0f}",
                                    className="display-3",
                                ),
                            ],
                            className="text-center",
                        )
                    ),
                    width=3,
                    lg=3,
                    xs=12,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("Total interactions"),
                                html.Hr(className="my-2"),
                                html.H1(
                                    f"{data.interactions_counts.sum():.0f}",
                                    className="display-3",
                                ),
                            ],
                            className="text-center",
                        )
                    ),
                    width=3,
                    lg=3,
                    xs=12,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("Interactions per case"),
                                html.Hr(className="my-2"),
                                html.H1(
                                    f"{100*data.interactions_counts.sum() / data.case_id.count():.2f}%",
                                    className="display-3",
                                ),
                            ],
                            className="text-center",
                        )
                    ),
                    width=3,
                    lg=3,
                    xs=12,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("Cases with nb"),
                                html.Hr(className="my-2"),
                                html.H1(
                                    total_cases_with_phone_nb,
                                    className="display-3",
                                ),
                            ],
                            className="text-center",
                        )
                    ),
                    width=3,
                    lg=3,
                    xs=12,
                ),
            ],
            className="mb-2",
        )

        data_output = {}
        for county, county_data in data.groupby("court_name"):
            data_output[county] = {
                "cases": county_data.case_id.count(),
                "interactions": f"{county_data.interactions_counts.sum():.0f}",
                "interactions_per_case": f"{100*county_data.interactions_counts.sum() / county_data.case_id.count():.2f}%",
                "cases_with_phone_nb": f"{100*county_data.phone.map(lambda x: 1 if 'no' not in x.lower() else 0).sum() / county_data.case_id.count():.2f}%",
            }

        data_output_df = pd.DataFrame(data_output).T

        stats_for_each_county = tables.make_bs_table(data_output_df)

        return (
            overview,
            leads_by_country,
            leads_by_status,
            interactions_by_date,
            stats_for_each_county,
        )
    else:
        return (
            html.Div(),
            empty_figure("No data to show"),
            empty_figure("No data to show"),
            empty_figure("No data to show"),
            html.Div(),
        )
