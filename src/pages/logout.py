import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

dash.register_page(__name__, class_icon="ti ti-user", order=6)


def layout():
    return dbc.Row(
        dbc.Col(
            [
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Logout", className="card-title"),
                            html.P(
                                "Click on the below button to logout",
                                className="card-text",
                                id="logout-output",
                            ),
                            dbc.Button(
                                "Logout",
                                id="logout-button",
                                color="primary",
                                className="mr-1",
                            ),
                            dcc.Location(id="url", refresh="callback-nav"),
                        ]
                    )
                )
            ]
        )
    )
