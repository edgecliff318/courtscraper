import dash
import dash_mantine_components as dmc
from dash import html

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
        ],
        style={"overflow": "hidden"},
    )
    skeleton_card = html.Div(
        dmc.Skeleton(
            height="400px",
            width="90vw",
        ),
        style={"overflow": "hidden"},
    )
    return html.Div(
        [
            dmc.Grid(
                [
                    dmc.Col(
                        dmc.Card(
                            [
                               [
                                    stats_controls,
                                    # html.Div(id="monitoring-status"),
                                ]
                            ],
                        ),
                        span=12,
                        className="mb-2 p-1",
                    ),
                    dmc.Col(
                        [
                            dmc.Title("Inbound Overview", order=2),
                            dmc.Text(
                                "Inbound leads summary for customers and leads that submitted a form on the website."
                            ),
                            html.Div(
                                children=skeleton_cards,
                                id="overview-inbound-summary",
                                style={"overflow": "auto"},
                            ),
                        ],
                        span=12,
                        className="mb-2 p-1",
                    ),
                    dmc.Col(
                          [
                            dmc.Title("Outbound Summary", order=2),
                            dmc.Text("Leads that were contacted by SMS or Phone Call."),
                            html.Div(
                                children=skeleton_cards,
                                id="overview-message-summary",
                            ),
                        ],
                        span=12,
                        className="mb-2 p-1",
                    ),
        
                    dmc.Col(
                        dmc.Card(
                            [
                                    html.Div(
                                        children=skeleton_card,
                                        id="graph-container-leads-state",
                                    )
                                ]
                        ),
                        span=12,
                        className="mb-2 p-1",
                    ),
                    dmc.Col(
                        dmc.Card(
                            [
                                    html.Div(
                                        children=skeleton_card,
                                        id="graph-container-leads-status",
                                    )
                                ]
                        ),
                        span=12,
                        className="mb-2 p-1",
                    ),
                    dmc.Col(
                        dmc.Card(
                             [
                                    html.Div(
                                        children=skeleton_card,
                                        id="graph-container-call",
                                    )
                                ]
                        ),
                        span=12,
                        className="mb-2 p-1",
                    ),
                ]
            ),
        ]
    )