import dash
import dash_mantine_components as dmc
from dash import html

from src.components.filters import stats_controls

dash.register_page(__name__, class_icon="ti ti-dashboard", order=2)


def layout():
    return html.Div(
        [
            dmc.Grid(
                [
                    dmc.Col(
                        dmc.Card(
                            [
                                stats_controls,
                                html.Div(id="monitoring-status"),
                            ],
                            style={"overflow": "auto"},
                        ),
                        span=12,
                        className="mb-2",
                        style={"overflow": "auto"},
                    ),
                    dmc.Col(
                        [
                            dmc.Title("Inbound Overview", order=2),
                            dmc.Text(
                                "Inbound leads summary for customers and leads that submitted a form on the website."
                            ),
                            html.Div(
                                [
                                    dmc.Skeleton(
                                        visible=False,
                                        children=html.Div(
                                            id="overview-inbound-summary",
                                        ),
                                        mb=10,
                                    ),
                                ]
                            ),
                        ],
                        span=12,
                        className="mb-2",
                    ),
                    dmc.Col(
                        [
                            dmc.Title("Outbound Summary", order=2),
                            dmc.Text(
                                "Leads that were contacted by SMS or Phone Call."
                            ),
                            dmc.Skeleton(
                                visible=False,
                                # visible=True,
                                children=html.Div(
                                    id="overview-message-summary",
                                ),
                                mb=10,
                            ),
                        ],
                        span=12,
                        className="mb-2",
                    ),
                    dmc.Col(
                        [
                            dmc.Title("Scraping Overview", order=2),
                            dmc.Text(
                                "Scraping summary for all scrapers by State."
                            ),
                            html.Div(
                                dmc.Skeleton(
                                    visible=False,
                                    children=html.Div(id="scrapper-summary"),
                                )
                            ),
                        ],
                        span=12,
                        className="mb-2",
                    ),
                    dmc.Col(
                        dmc.Card(
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
                        ),
                        span=12,
                        className="mb-2",
                    ),
                    dmc.Col(
                        dmc.Card(
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
                        span=12,
                        className="mb-2",
                    ),
                    dmc.Col(
                        dmc.Card(
                            [
                                html.Div(
                                    [
                                        dmc.Skeleton(
                                            visible=False,
                                            children=html.Div(
                                                id="graph-container-call",
                                            ),
                                            mb=10,
                                        ),
                                    ]
                                )
                            ]
                        ),
                        span=12,
                        className="mb-2",
                    ),
                ]
            ),
        ]
    )
