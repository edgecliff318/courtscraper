import logging
from datetime import date, datetime

import dash
import dash_mantine_components as dmc
from dash import html

logger = logging.Logger(__name__)

dash.register_page(__name__, class_icon="ti ti-file", order=2)


def layout():
    # Add the summary card with the number of leads
    summary_card = html.Div(
        dmc.Skeleton(
            visible=False,
            children=html.Div(id="leads-inbound-summary"),
        )
    )

    # Add the card with filters with dates and status
    filters_card = dmc.Card(
        [
            dmc.CardSection(
                dmc.Group(
                    [
                        dmc.DateRangePicker(
                            id="leads-inbound-date-picker",
                            label="Select a date range",
                            minDate=date(2023, 12, 20),
                            value=[
                                datetime.now().date(),
                                datetime.now().date(),
                            ],
                            dropdownPosition="bottom",
                            style={"width": "300px"},
                        ),
                        dmc.MultiSelect(
                            label="Select leads with status",
                            placeholder="Select all that apply",
                            id="leads-inbound-status",
                            value=["all"],
                            data=[
                                {"value": "all", "label": "All"},
                            ],
                            dropdownPosition="bottom",
                        ),
                        dmc.Button(
                            id="leads-inbound-apply-filters",
                            children="Apply filters",
                            color="dark",
                            size="sm",
                            # Align bottom
                            className="mt-auto",
                        ),
                    ]
                ),
                className="m-2",
            )
        ],
        shadow="sm",
        radius="md",
        style={"overflow": "visible"},
    )

    # Add the card for the leads
    leads_card = dmc.Card(
        [
            dmc.CardSection(
                dmc.Text("Leads List", weight=500),
                withBorder=True,
                inheritPadding=True,
                py="xs",
            ),
            dmc.CardSection(
                dmc.Skeleton(
                    visible=False,
                    children=html.Div(id="leads-inbound-table"),
                ),
                className="m-2",
                style={"overflow": "visible"},
            ),
        ],
        style={"overflow": "visible"},
    )

    # Add the card
    output = dmc.Grid(
        children=[
            dmc.Col(html.Div("leads-inbound-alerts"), span=12),
            dmc.Col(filters_card, span=12),
            dmc.Col(summary_card, span=12),
            dmc.Col(leads_card, span=12),
        ],
        gutter="xl",
    )

    return output
