import logging

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

from src.components.filters import cases_controls

logger = logging.Logger(__name__)

dash.register_page(__name__, order=3, path_template="/manage/actions")


def layout():
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    cases_controls,
                                ]
                            ),
                        ),
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
            ###
            html.Div(id="actions-data"),
            dmc.Grid(
                children=[
                    dmc.GridCol(
                        dmc.Card(
                            children=[
                                dmc.Group(
                                    [
                                        DashIconify(
                                            icon="ri:todo-line", width=20
                                        ),
                                        dmc.Title("To-do", order=2),
                                    ]
                                ),
                                html.Div(
                                    id="case_card_col_todo",
                                    style={"overflowY": "auto"},
                                ),
                            ],
                        ),
                        span={"xl": 4, "lg": 4, "md": 12, "sm": 12, "xs": 12},
                    ),
                    dmc.GridCol(
                        dmc.Card(
                            children=[
                                dmc.Group(
                                    [
                                        DashIconify(
                                            icon="ri:time-fill",
                                            width=20,
                                        ),
                                        dmc.Title("Pending", order=2),
                                    ]
                                ),
                                html.Div(
                                    id="case_card_col_pending",
                                    style={"overflowY": "auto"},
                                ),
                            ],
                        ),
                        span={"xl": 4, "lg": 4, "md": 12, "sm": 12, "xs": 12},
                    ),
                    dmc.GridCol(
                        dmc.Card(
                            children=[
                                dmc.Group(
                                    [
                                        DashIconify(
                                            icon="fluent-mdl2:completed-solid",
                                            width=20,
                                        ),
                                        dmc.Title("Closed Recently", order=2),
                                    ]
                                ),
                                html.Div(
                                    id="case_card_col_closed",
                                    style={"overflowY": "auto"},
                                ),
                            ],
                        ),
                        span={"xl": 4, "lg": 4, "md": 12, "sm": 12, "xs": 12},
                    ),
                ],
                justify="center",
                align="flex-start",
                gutter="xl",
            ),
        ],
        style={"padding": "20px"},
    )
