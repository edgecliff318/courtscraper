import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(__name__, class_icon="ti ti-home", order=1, path="/")


def layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3("Welcome to Ticket Washer !", className="display-3"),
                html.P(
                    "Use it to process ticket data!",
                    className="lead",
                ),
                html.Hr(className="my-2"),
                html.P(
                    "A new AI model for automatic ticket processing "
                    "was implemented."
                ),
                html.P(
                    dbc.Button("Learn more", color="primary"), className="lead"
                ),
            ],
        ),
    )
