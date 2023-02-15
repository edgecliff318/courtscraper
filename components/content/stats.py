import dash_bootstrap_components as dbc
import dash.html as html
from dash import dcc


def page(data=None):
    overview = html.Div(
        id="overview"
    )

    leads_by_county = dbc.Card(
        dbc.CardBody(
            [
                html.H3("Leads By County"),
                html.Hr(className="my-2"),
                dcc.Graph(
                    id="leads-by-county",
                )
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
                )
            ],
        ),
    )

    stats_for_each_county = dbc.Card(
        dbc.CardBody(
            [
                html.H3("Stats For Each County"),
                html.Hr(className="my-2"),
                html.Div(
                    id="stats-for-each-county"
                )
            ],
        ),
    )

    return dbc.Row(
        [
            dcc.Interval(
                id='interval-component',
                interval=1000*1000,  # in milliseconds
                n_intervals=0
            ),
            overview,
            dbc.Col(
                [
                    leads_by_county
                ],
                md=12,
            ),
            dbc.Col(
                [
                    interactions_by_date
                ],
                md=12,
            ),
            dbc.Col(
                [
                    stats_for_each_county
                ],
                md=12,
            ),
        ]
    )
