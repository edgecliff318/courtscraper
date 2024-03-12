import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html

from src.components.inputs import generate_form_group

dash.register_page(__name__, class_icon="ti ti-home", order=1, path="/")


def layout(data=None):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3("Welcome to Ticket Washer !", className="display-3"),
                html.H4("Look up a case"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                generate_form_group(
                                    label="Case Number",
                                    id="case-number",
                                    placeholder="Put the case number",
                                    type="Input",
                                    className="m-1",
                                ),
                                html.Div(
                                    generate_form_group(
                                        label="Court",
                                        id="court-selector-overview",
                                        placeholder="Select a Court",
                                        type="Dropdown",
                                        options=[],
                                        value=None,
                                        multi=True,
                                        persistence_type="session",
                                        persistence=True,
                                    ),
                                    className="m-1",
                                    style={"min-width": "50%"},
                                ),
                            ],
                            width=6,
                            class_name="d-flex align-items-left",
                        ),
                    ],
                    className="mb-1",
                ),
                html.H4(
                    "Look up using the first name / last name",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                generate_form_group(
                                    label="First Name",
                                    id="first-name-search",
                                    placeholder="First Name",
                                    type="Input",
                                    className="m-1",
                                ),
                                generate_form_group(
                                    label="Middle Name",
                                    id="middle-name-search",
                                    placeholder="Middle Name",
                                    type="Input",
                                    className="m-1",
                                ),
                                generate_form_group(
                                    label="Last Name",
                                    id="last-name-search",
                                    placeholder="Last Name",
                                    type="Input",
                                    className="m-1",
                                ),
                            ],
                            width=6,
                            class_name="d-flex align-items-left",
                        ),
                    ],
                    className="mb-1",
                ),
                html.P(
                    dmc.Button(
                        "Look up",
                        className="m-1",
        
                        id="search-button",
                    ),
                    className="lead",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            id="search-results",
                            width=12,
                        )
                    ]
                ),
            ],
        ),
    )
