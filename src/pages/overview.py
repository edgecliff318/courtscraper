import dash_bootstrap_components as dbc
import dash.html as html


def layout(data=None):
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
