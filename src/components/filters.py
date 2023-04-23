import dash_bootstrap_components as dbc
from dash import html

from src.components.inputs import generate_form_group

leads_controls = dbc.Row(
    [
        dbc.Col(
            html.H3("Courts", className="align-middle"), width=1, xs=12, lg=1
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
            xs=12,
            lg=5,
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
            xs=12,
            lg=3,
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
                    {"label": "New", "value": "new"},
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
            xs=12,
            lg=2,
        ),
        dbc.Col(dbc.Button("Leads", id="leads-button"), width=1, lg=1, xs=12),
    ]
)
