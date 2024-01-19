import dash
import dash_bootstrap_components as dbc
from dash import html
import dash_mantine_components as dmc
from src.components.filters import stats_controls


dash.register_page(__name__, class_icon="ti ti-dashboard", order=2)


def layout():
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    stats_controls,
                                    html.Div(id="monitoring-status"),
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            dmc.Skeleton(
                                visible=False,
                                children=html.Div(id="scrapper-summary"),
                            )
                        ),
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            dmc.Skeleton(
                                                visible=False,
                                                # visible=True,
                                                children=html.Div(
                                                    id="overview-test",
                                                ),
                                                mb=10,
                                            ),
                                        ]
                                    )
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
            ###
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            dmc.Skeleton(
                                                visible=False,
                                                # visible=True,
                                                children=html.Div(
                                                    id="overview",
                                                ),
                                                mb=10,
                                            ),
                                        ]
                                    )
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
            
        #graph leads state
         dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            dmc.Skeleton(
                                                visible=False,
                                                children=html.Div(
                                                    id="graph-container-leads-state",
                                                ),
                                                mb=10,
                                            ),
                                        ]
                                    )
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
            # leads status
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            dmc.Skeleton(
                                                visible=False,
                                                children=html.Div(
                                                    id="graph-container-leads-status",
                                                ),
                                                mb=10,
                                            ),
                                        ]
                                    )
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
        ]
    )
