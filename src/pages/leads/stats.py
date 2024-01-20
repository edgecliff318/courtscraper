import dash
from dash import html
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from src.components.filters import stats_controls


dash.register_page(__name__, class_icon="ti ti-dashboard", order=2)


def layout():
    skeleton_cards = dmc.Grid(
        children=[
            dmc.Col(
                dmc.Skeleton(
                    height="150px",
                    width="23vw",
                ),
                md=3,
            )
            for i in range(4)
        ]
    )
    skeleton_card = dmc.Skeleton(
        height="400px",
        width="90vw",
    )
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
                        className="mb-2 p-1",
                        style={"overflow": "auto"},
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dmc.Title("Inbound Overview", order=2),
                            dmc.Text(
                                "Inbound leads summary for customers and leads that submitted a form on the website."
                            ),
                            html.Div(
                                children=skeleton_cards,
                                id="overview-inbound-summary",
                            ),
                        ],
                        width=12,
                        className="mb-2 p-1",
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dmc.Title("Outbound Summary", order=2),
                            dmc.Text("Leads that were contacted by SMS or Phone Call."),
                            html.Div(
                                children=skeleton_cards,
                                id="overview-message-summary",
                            ),
                        ],
                        width=12,
                        className="mb-2 p-1",
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
                                        children=skeleton_card,
                                        id="graph-container-leads-state",
                                    )
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2 p-1",
                        style={"overflow": "auto"},
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
                                        children=skeleton_card,
                                        id="graph-container-leads-status",
                                    )
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2 p-1",
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
                                        children=skeleton_card,
                                        id="graph-container-call",
                                    )
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2 p-1",
                    ),
                ]
            ),
        ]
    )
