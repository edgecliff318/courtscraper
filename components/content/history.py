import dash_bootstrap_components as dbc
import dash.html as html


def page(data=None):
    return html.Div(
        dbc.Container(
            [
                html.H1("Welcome to Ticket Flusher !", className="display-3"),
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
            fluid=True,
            className="py-3",
        ),
        className="p-3 bg-light rounded-3",
    )
