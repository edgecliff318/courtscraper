import dash.html as html
import dash_bootstrap_components as dbc

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
                                generate_form_group(
                                    label="Measure",
                                    id="court-selector",
                                    placeholder="Select a Court",
                                    type="Dropdown",
                                    options=[],
                                    value=None,
                                    multi=True,
                                    persistence_type="session",
                                    persistence=True,
                                ),
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
