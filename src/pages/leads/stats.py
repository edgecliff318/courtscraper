import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from src.components.filters import leads_controls

dash.register_page(__name__, class_icon="ti ti-dashboard", order=2)


def layout():
    overview = html.Div(id="overview")

    leads_by_county = dbc.Card(
        dbc.CardBody(
            [
                html.H3("Leads By County"),
                html.Hr(className="my-2"),
                dcc.Graph(
                    id="leads-by-county",
                ),
            ],
        ),
    )

    leads_by_status = dbc.Card(
        dbc.CardBody(
            [
                html.H3("Leads By Status"),
                html.Hr(className="my-2"),
                dcc.Graph(
                    id="leads-by-status",
                ),
            ],
        ),
    )

    interactions_by_date = dbc.Card(
        dbc.CardBody(
            [
                html.H3("Interactions By Date"),
                html.Hr(className="my-2"),
                dcc.Graph(
                    id="interactions-by-date",
                ),
            ],
        ),
    )

    stats_for_each_county = dbc.Card(
        dbc.CardBody(
            [
                html.H3("Stats For Each County"),
                html.Hr(className="my-2"),
                html.Div(id="stats-for-each-county"),
            ],
        ),
    )

    return dbc.Row(
        [
            dcc.Interval(
                id="interval-component",
                interval=1000 * 1000,  # in milliseconds
                n_intervals=0,
            ),
            leads_controls,
            overview,
            dbc.Col(
                [leads_by_county],
                md=6,
                class_name="mb-2",
            ),
            dbc.Col(
                [leads_by_status],
                md=6,
                class_name="mb-2",
            ),
            dbc.Col(
                [interactions_by_date],
                md=12,
                class_name="mb-2",
            ),
            dbc.Col(
                [stats_for_each_county],
                md=12,
                class_name="mb-2",
            ),
        ]
    )
