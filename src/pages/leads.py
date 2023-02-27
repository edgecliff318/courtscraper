import logging

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from src.components.figures import empty_figure
from src.components.inputs import generate_form_group

logger = logging.Logger(__name__)

dash.register_page(__name__, class_icon="ti ti-file", order=2)


def layout():
    controls = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.H3("Courts", className="align-middle"), width=1
                    ),
                    dbc.Col(
                        generate_form_group(
                            label="Measure",
                            id="court-selector",
                            placeholder="Select a Court",
                            type="Dropdown",
                            options=[],
                            value="0",
                            multi=True,
                            persistence_type="session",
                            persistence=True,
                        ),
                        width=5,
                    ),
                    dbc.Col(
                        generate_form_group(
                            label="Date",
                            id="date-selector",
                            placeholder="Select a Date",
                            type="DateRangePicker",
                            persistence_type="session",
                            persistence=True,
                        ),
                        width=3,
                    ),
                    dbc.Col(
                        generate_form_group(
                            label="Interaction",
                            id="lead-status-selector",
                            placeholder="Select the type",
                            type="Select",
                            persistence_type="session",
                            persistence=True,
                            value="not_contacted",
                            options=[
                                {"label": "All", "value": "all"},
                                {"label": "Contacted", "value": "contacted"},
                                {"label": "Responded", "value": "responded"},
                                {"label": "Converted", "value": "converted"},
                                {
                                    "label": "Not Contacted",
                                    "value": "not_contacted",
                                },
                            ],
                        ),
                        width=2,
                    ),
                    dbc.Col(dbc.Button("Leads", id="leads-button"), width=1),
                ]
            )
        ]
    )
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
                        width=12,
                        className="mb-2",
                    ),
                ]
            ),
            dbc.Row([], id="cases-data"),
            dbc.Row([], id="leads-data"),
        ]
    )
