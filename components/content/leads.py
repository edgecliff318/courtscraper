import os
import dash_bootstrap_components as dbc
import logging

from dash import html

import components
from components.figures import empty_figure

logger = logging.Logger(__name__)


def page():
    controls = html.Div([
        dbc.Row(
            [
                dbc.Col(html.H3("Courts", className="align-middle"),
                        width=1),
                dbc.Col(
                    components.inputs.generate_form_group(
                        label="Measure",
                        id="court-selector",
                        placeholder="Select a Court",
                        type="Dropdown", options=[],
                        value="0",
                        multi=True
                    ),
                    width=8
                ),
                dbc.Col(
                    components.inputs.generate_form_group(
                        label="Date",
                        id="date-selector",
                        placeholder="Select a Date",
                        type="DatePickerSingle"
                    ),
                    width=2
                ),
                dbc.Col(
                    dbc.Button("Search", id="search-button"),
                    width=1
                )
            ]
        )
    ])
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    controls,
                                ]
                            ),
                        ),
                        width=12
                    ),

                ]
            ),
            dbc.Row(
                [],
                id="cases-data"
            )
        ]
    )

def single():
    return dbc.Row(
        id="lead-single"
    )
