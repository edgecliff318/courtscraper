from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

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


def create_date_form_group(id: str):
    return generate_form_group(
        label="Date",
        id=id,
        placeholder="Select a Date",
        type="DateRangePicker",
        persistence_type="session",
        persistence=True,
        start_date=(datetime.now() - timedelta(days=0)).strftime("%Y-%m-%d"),
        end_date=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
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


def create_scrapper_form_group():
    return generate_form_group(
        label="Scrapper",
        id="scrapper-selector",
        placeholder="Select the Scrapper",
        type="Select",
        persistence_type="session",
        persistence=True,
        value="scrapper1",
        options=[
            {"label": "scrapper1", "value": "scrapper1"},
            {"label": "scrapper2", "value": "scrapper2"},
            {"label": "scrapper3", "value": "scrapper3"},
        ],
    )


def create_button(label, id, width, lg, xs):
    return dbc.Col(
        dmc.Button(
            label, id=id, color="dark", size="sm", className="mt-auto "
        ),
        width=width,
        lg=lg,
        xs=xs,
        className="d-flex mx-2",
    )


def create_switch():
    return html.Div(
        [
            dmc.Text(
                "Automated Messaging",
                id="switch-settings-txt",
                w=500,
                c="dark",
            ),
            dmc.Space(h=10),
            dmc.Switch(
                id="switch-automated_message",
                thumbIcon=DashIconify(
                    icon="mdi:workflow",
                    width=16,
                    color=dmc.DEFAULT_THEME["colors"]["teal"][5],
                ),
                size="md",
                color="teal",
                checked=True,
            ),
        ]
    )


monitoring_controls = dmc.Grid(
    children=[
        dmc.GridCol(
            create_date_form_group("monitoring-date-selector"),
            span="content",
            style={
                "minWidth": "250px",
            },
        ),
        dmc.GridCol(
            create_interaction_form_group(),
            span="content",
            style={
                "minWidth": "250px",
            },
        ),
        dmc.GridCol(
            dmc.Button(
                "Monitoring",
                id="monitoring-button",
                color="dark",
            ),
            span="content",
        ),
        dmc.GridCol(
            dmc.Button(
                "Refresh",
                id="monitoring-refresh-button",
                color="dark",
            ),
            span="content",
        ),
        dmc.GridCol(create_switch(), span="content"),
    ],
    justify="flex-start",
    align="flex-end",
    gutter="xl",
)


stats_controls = dbc.Row(
    [
        dbc.Col(
            create_date_form_group("stats-date-selector"),
            width=3,
            xs=12,
            lg=3,
        ),
        create_button("Run", "stats-refresh-button", 1, 1, 6),
    ],
    justify="left",
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

cases_controls = dbc.Row([generate_col(court_selector, lg=5)])
