import dash.html as html
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from src.components.filters import get_court_selector
from src.components.inputs import generate_form_group


def layout(data=None):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3("Welcome to Ticket Washer !", className="display-3"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                generate_form_group(
                                    label="Case Number",
                                    id="case-number",
                                    placeholder="Set the phone number",
                                    type="Input",
                                )
                            ],
                            width=3,
                        ),
                        dbc.Col(
                            [
                                get_court_selector(),
                            ],
                            width=3,
                        ),
                    ],
                    className="mb-1",
                ),
                dbc.Row(
                    [
                        dbc.Col("Email", width=4),
                        dbc.Col(
                            [
                                generate_form_group(
                                    label="Email",
                                    id="lead-single-email",
                                    placeholder="Set the email",
                                    type="Input",
                                )
                            ],
                            width=8,
                        ),
                    ],
                    className="mb-1",
                ),
                html.P(
                    dbc.Button("Learn more", color="primary"), className="lead"
                ),
            ],
        ),
    )
