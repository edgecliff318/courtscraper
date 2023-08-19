from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
from dash import html

from src.components.inputs import generate_form_group
from src.models import leads as leads_model

leads_controls = dbc.Row(
    [
        dbc.Col(
            generate_form_group(
                label="Courts",
                id="court-selector",
                placeholder="Select a Court",
                type="Dropdown",
                options=[],
                value=None,
                multi=True,
                persistence_type="session",
                persistence=True,
            ),
            width=5,
            xs=12,
            lg=6,
        ),
        dbc.Col(
            generate_form_group(
                label="Date",
                id="date-selector",
                placeholder="Select a Date",
                type="DateRangePicker",
                persistence_type="session",
                persistence=True,
                start_date=(datetime.now() - timedelta(days=1)).strftime(
                    "%Y-%m-%d"
                ),
                end_date=datetime.now().strftime("%Y-%m-%d"),
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
                options=leads_model.leads_statuses,
            ),
            width=2,
            xs=12,
            lg=2,
        ),
        # dbc.Col(dbc.Button("Leads", id="leads-button"), width=1, lg=1, xs=12),
    ]
)


monitoring_controls = dbc.Row(
    [
        dbc.Col(
            generate_form_group(
                label="Date",
                id="monitoring-date-selector",
                placeholder="Select a Date",
                type="DateRangePicker",
                persistence_type="session",
                persistence=True,
                # set the start date, end date to the yesterday and today
                # respectively
                start_date=(datetime.now() - timedelta(days=1)).strftime(
                    "%Y-%m-%d"
                ),
                end_date=datetime.now().strftime("%Y-%m-%d"),
            ),
            width=3,
            xs=12,
            lg=3,
        ),
        dbc.Col(
            generate_form_group(
                label="Interaction",
                id="monitoring-status-selector",
                placeholder="Select the type",
                type="Select",
                persistence_type="session",
                persistence=True,
                value="all",
                options=[
                    {
                        "label": "All",
                        "value": "all",
                    },
                    {"label": "Inbound", "value": "inbound"},
                    {"label": "Outbound", "value": "outbound"},
                ],
            ),
            width=2,
            xs=12,
            lg=2,
        ),
        dbc.Col(
            dbc.Button("Monitoring", id="monitoring-button"),
            width=1,
            lg=1,
            xs=6,
        ),
        dbc.Col(
            dbc.Button("Refresh", id="monitoring-refresh-button"),
            width=1,
            lg=1,
            xs=6,
        ),
    ]
)
