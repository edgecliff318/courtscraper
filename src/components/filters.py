from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
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
                start_date=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
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


def create_date_form_group():
    return generate_form_group(
        label="Date",
        id="monitoring-date-selector",
        placeholder="Select a Date",
        type="DateRangePicker",
        persistence_type="session",
        persistence=True,
        start_date=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        end_date=datetime.now().strftime("%Y-%m-%d"),
    )

def create_interaction_form_group():
    return generate_form_group(
        label="Interaction",
        id="monitoring-status-selector",
        placeholder="Select the type",
        type="Select",
        persistence_type="session",
        persistence=True,
        value="all",
        options=[
            {"label": "All", "value": "all"},
            {"label": "Inbound", "value": "inbound"},
            {"label": "Outbound", "value": "outbound"},
        ],
    )

def create_button(label, id, width, lg, xs):
    return dbc.Col(
        dmc.Button(
            label,
            id=id,
            color="dark",
            size="sm",
            className="mt-auto"  # Align bottom using margin-top auto
        ),
        width=width,
        lg=lg,
        xs=xs,
        className="d-flex"  # Flex container for vertical alignment
    )

def create_switch():
    return html.Div(
    [
        dmc.Text("Automated Messaging", id="switch-settings-txt", weight=500,color="dark"),
        dmc.Space(h=10),
        dmc.Switch(
            id="switch-automated_message", 
        thumbIcon=DashIconify(
            icon="mdi:workflow", 
            width=16, 
            color=dmc.theme.DEFAULT_COLORS["teal"][5]
        ),
        size="md",
        color="teal",
        checked=True,
    ),
        
    ]
)




    
monitoring_controls = dbc.Row(
    [
        dbc.Col(create_date_form_group(), width=3, xs=12, lg=3),
        dbc.Col(create_interaction_form_group(), width=2, xs=12, lg=2),
        create_button("Monitoring", "monitoring-button", 1, 1, 6),
        create_button("Refresh", "monitoring-refresh-button", 1, 1, 6),
        dbc.Col(create_switch(), width=2, lg=2, xs=12, className="d-flex align-items-center")

    ],
    justify="center"  
)


def generate_col(content, **kwargs):
    """Generate a column with specified width configurations."""
    width_config = {
        "width": 4,
        "xs": 12,
        "lg": kwargs.get("lg", 4),
    }
    return dbc.Col(content, **width_config)


court_selector = generate_form_group(
    label="Courts",
    id="court-selector",
    placeholder="Select a Court",
    type="Dropdown",
    options=[],
    value=None,
    multi=True,
    persistence_type="session",
    persistence=True,
)

date_selector = generate_form_group(
    label="Date",
    id="date-selector",
    placeholder="Select a Date",
    type="DateRangePicker",
    persistence_type="session",
    persistence=True,
    start_date=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
    end_date=datetime.now().strftime("%Y-%m-%d"),
)

cases_controls = dbc.Row(
    [generate_col(court_selector, lg=5), generate_col(date_selector)]
)
