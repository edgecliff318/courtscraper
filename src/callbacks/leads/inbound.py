import json
import logging

import dash
import dash.html as html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
from dash import ALL, MATCH, Input, Output, callback, html
from dash_iconify import DashIconify

from src.components.cards import render_stats_card
from src.connectors.cloudtalk import add_website_lead
from src.core.config import get_settings
from src.core.format import humanize_phone
from src.services import leads

logger = logging.Logger(__name__)

settings = get_settings()


def process_lead(lead):
    if lead.get("court", None) is not None:
        lead["court_id"] = lead.get("court", {}).get("court_id")
        lead["court"] = lead.get("court", {}).get("court_name")
    if lead.get("violation", None) is not None:
        lead["violation_id"] = lead.get("violation", {}).get("violation_id")
        lead["violation"] = lead.get("violation", {}).get("violation_name")

    lead["user"] = lead.get("user_id") is not None

    # Creation date from ms timestamp
    try:
        creation_date = pd.to_datetime(lead.get("creation_date"), unit="ms")
    except Exception as e:
        logger.error(f"Error parsing creation_date: {e}")
        creation_date = pd.to_datetime(lead.get("creation_date"))

    # UTC to Central time
    creation_date = creation_date.tz_convert("America/Chicago")
    creation_date = creation_date.strftime("%Y-%m-%d %H:%M:%S")

    lead["creation_date"] = creation_date

    return lead


def render_inbound_summary(data: pd.DataFrame):
    # Total leads
    total_leads = len(data)

    # Total leads by status
    total_leads_by_status = data.groupby("status").size().to_dict()

    return dmc.Grid(
        [
            dmc.Col(
                render_stats_card(
                    "Total leads",
                    f"{total_leads:,}",
                    "leads",
                ),
                md=4,
            ),
            dmc.Col(
                render_stats_card(
                    "New Leads",
                    f"{total_leads_by_status.get('new', 0):,}",
                    "leads",
                ),
                md=4,
            ),
            dmc.Col(
                render_stats_card(
                    "Leads Processed",
                    f"{(total_leads - total_leads_by_status.get('new', 0)):,}",
                    "leads",
                ),
                md=4,
            ),
        ]
    )


def render_inbound_table(data: pd.DataFrame):
    header = [
        html.Thead(
            html.Tr(
                [
                    html.Th("State"),
                    html.Th("Court"),
                    html.Th("Violation"),
                    html.Th("Phone"),
                    html.Th("Date"),
                    html.Th("Accident"),
                    html.Th("CDL"),
                    html.Th("Ticket"),
                    html.Th("User"),
                    html.Th("Status"),
                    html.Th("Actions"),
                ]
            )
        )
    ]

    rows = []

    for _, row in data.iterrows():
        state_badge = dmc.Badge(
            row.state,
            color="indigo",
            size="sm",
            className="mr-2",
        )

        if row.court is not None:
            court_badge = dmc.Badge(
                row.court,
                color="indigo",
                size="sm",
                className="mr-2",
            )
        else:
            court_badge = dmc.Badge(
                "No court",
                color="gray",
                size="sm",
                className="mr-2",
            )

        # Ticket image hover
        if row.ticket_img is not None:
            ticket_hover = dmc.HoverCard(
                children=[
                    dmc.HoverCardTarget(
                        html.A(
                            DashIconify(
                                icon="tdesign:ticket",
                                color="indigo",
                            ),
                            href=row.ticket_img,
                        )
                    ),
                    dmc.HoverCardDropdown(
                        children=[
                            dmc.Image(
                                src=row.ticket_img,
                                width="100%",
                            ),
                        ],
                        style={"width": "300px"},
                    ),
                ]
            )
        else:
            ticket_hover = DashIconify(
                icon="material-symbols-light:no-sim-sharp",
                color="gray",
            )

        if row.user_id is not None:
            user_icon = DashIconify(
                icon="mdi:account-check",
                color="green",
            )
            # Click to open user

            url = "https://dashboard.clerk.com/apps/app_2ZdvAxwBHjl6An4cHq9vA6RFjTG/instances/ins_2ZdvJ8q3S8eoqpO6Kr93wY3LJ5A/users/"
            user_icon = html.A(
                user_icon,
                href=f"{url}{row.user_id}",
                target="_blank",
            )

        else:
            user_icon = DashIconify(
                icon="system-uicons:no-sign",
                color="gray",
            )

        if row.violation is not None:
            violation = dmc.Text(row.violation, size="sm")

        else:
            violation = dmc.Text("No violation", size="sm", color="gray")

        creation_date = dmc.Text(row.creation_date, size="sm")

        accident_checkbox = dmc.Checkbox(
            checked=row.accidentCheckbox, disabled=True, size="xs"
        )

        commercial_driver_licence = dmc.Checkbox(
            checked=row.commercialDriverLicence, disabled=True, size="xs"
        )

        status = dmc.Select(
            id={
                "type": "leads-inbound-status",
                "index": row.id,
            },
            value=row.status,
            data=[
                {"value": "new", "label": "New"},
                {"value": "contacted", "label": "Contacted"},
                {"value": "lost", "label": "Lost"},
                {"value": "converted", "label": "Converted"},
            ],
            size="xs",
            className="m-0",
        )

        # Remove button
        remove_button = dmc.ActionIcon(
            DashIconify(icon="mdi:trash-can-outline", width=20),
            size="xs",
            variant="filled",
            id={
                "type": "leads-inbound-remove",
                "index": row.id,
            },
            n_clicks=0,
        )

        if row.cloudtalk_upload:
            cloudtalk_icon = dmc.ActionIcon(
                DashIconify(
                    icon="gg:phone",
                ),
                size="xs",
                variant="filled",
                id={
                    "type": "leads-inbound-cloudtalk",
                    "index": row.id,
                },
                n_clicks=0,
                disabled=True,
            )
        else:
            cloudtalk_icon = dmc.ActionIcon(
                DashIconify(
                    icon="gg:phone",
                ),
                size="xs",
                variant="filled",
                id={
                    "type": "leads-inbound-cloudtalk",
                    "index": row.id,
                },
                n_clicks=0,
            )

        rows.append(
            html.Tr(
                [
                    html.Td(state_badge),
                    html.Td(court_badge),
                    html.Td(violation),
                    html.Td(humanize_phone(row.phone)),
                    html.Td(creation_date),
                    html.Td(accident_checkbox),
                    html.Td(commercial_driver_licence),
                    html.Td(ticket_hover),
                    html.Td(user_icon),
                    html.Td(status),
                    html.Td(
                        dmc.Group(
                            [
                                cloudtalk_icon,
                                remove_button,
                                html.Div(
                                    id={
                                        "type": "leads-inbound-alers-single",
                                        "index": row.id,
                                    }
                                ),
                            ],
                            spacing="xs",
                        )
                    ),
                ],
                id={
                    "type": "leads-inbound-row",
                    "index": row.id,
                },
            )
        )

    return dmc.Table(
        header + [html.Tbody(rows)],
        highlightOnHover=True,
    )


@callback(
    Output("leads-inbound-table", "children"),
    Output("leads-inbound-summary", "children"),
    Input("leads-inbound-date-picker", "value"),
    Input("leads-inbound-status", "value"),
    Input("leads-inbound-apply-filters", "n_clicks"),
)
def render_inbound_leads(dates, status, n_clicks):
    (start_date, end_date) = dates
    if status == "all" or (isinstance(status, list) and "all" in status):
        status = None

    leads_list = leads.get_leads(
        start_date=start_date,
        end_date=end_date,
        status=status,
        source="website",
    )

    # Fields selection
    fields = {
        "id",
        "phone",
        "violation",
        "court",
        "accidentCheckbox",
        "commercialDriverLicence",
        "ticket_img",
        "user_id",
        "cloudtalk_upload",
        "state",
        "status",
        "creation_date",
    }

    leads_list = [
        process_lead(lead.model_dump(include=fields)) for lead in leads_list
    ]

    df = pd.DataFrame(leads_list)

    if df.empty:
        return [
            dmc.Alert(
                "No leads found",
                color="yellow",
                className="m-2",
            ),
            dash.no_update,
        ]

    return [
        render_inbound_table(df),
        render_inbound_summary(df),
    ]


# Callback to remove a lead


@callback(
    Output({"type": "leads-inbound-alers-single", "index": MATCH}, "children"),
    Output({"type": "leads-inbound-row", "index": MATCH}, "className"),
    Input({"type": "leads-inbound-remove", "index": MATCH}, "n_clicks"),
    Input({"type": "leads-inbound-cloudtalk", "index": MATCH}, "n_clicks"),
    Input(
        {"type": "leads-inbound-status", "index": MATCH},
        "value",
    ),
)
def remove_lead(n_clicks_remove, n_clicks_cloudtalk, status):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        # Json parse the button id
        button_id = json.loads(button_id)
        button_type = button_id.get("type")
        lead_id = button_id.get("index")
        if button_type == "leads-inbound-remove":
            leads.delete_lead(lead_id)
            return (
                dmc.Notification(
                    message="Lead deleted",
                    title="Success",
                    action="show",
                    id="leads-inbound-alert",
                    className="m-0",
                    icon=DashIconify(
                        icon="mdi:trash-can-outline",
                        width=20,
                        color="white",
                    ),
                ),
                "d-none",
            )
        elif button_type == "leads-inbound-status":
            leads.patch_lead(lead_id, status=status)
            return (
                dmc.Notification(
                    message="Lead status updated",
                    title="Success",
                    action="show",
                    id="leads-inbound-alert",
                    className="m-0",
                    icon=DashIconify(
                        icon="mdi:trash-can-outline",
                        width=20,
                        color="white",
                    ),
                    autoClose=1500,
                ),
                dash.no_update,
            )

        elif button_type == "leads-inbound-cloudtalk":
            fields = {
                "id",
                "phone",
                "violation",
                "court",
                "accidentCheckbox",
                "commercialDriverLicence",
                "ticket_img",
                "user_id",
                "cloudtalk_upload",
                "state",
                "status",
                "creation_date",
            }

            lead = leads.get_lead(lead_id, fields=fields)

            if lead is None:
                return (
                    dmc.Notification(
                        message="Lead not found",
                        title="Error",
                        action="show",
                        id="leads-inbound-alert",
                        className="m-0",
                        icon=DashIconify(
                            icon="mdi:alert-circle-outline",
                            width=20,
                            color="white",
                        ),
                    ),
                    dash.no_update,
                )

            if lead.cloudtalk_upload:
                return (
                    dmc.Notification(
                        message="Lead already uploaded to CloudTalk",
                        title="Error",
                        action="show",
                        id="leads-inbound-alert",
                        className="m-0",
                        icon=DashIconify(
                            icon="mdi:alert-circle-outline",
                            width=20,
                            color="white",
                        ),
                    ),
                    dash.no_update,
                )

            lead_dict = lead.model_dump(include=fields)

            lead_dict = process_lead(lead_dict)

            add_website_lead(
                lead_dict,
            )

            leads.patch_lead(lead_id, cloudtalk_upload=True)
            return (
                dmc.Notification(
                    message="Lead uploaded to CloudTalk",
                    title="Success",
                    action="show",
                    id="leads-inbound-alert",
                    className="m-0",
                    icon=DashIconify(
                        icon="mdi:phone",
                        width=20,
                        color="white",
                    ),
                ),
                dash.no_update,
            )
        else:
            raise dash.exceptions.PreventUpdate
