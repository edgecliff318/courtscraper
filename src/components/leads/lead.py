import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

from src.components.groups import create_group_item
from src.core.format import humanize_phone


def get_lead_card(lead):
    phones = [
        html.Div(
            [
                create_group_item(
                    label="Phone",
                    value=humanize_phone(phone.get("phone")),
                    icon="material-symbols:phone-android-outline",
                ),
                dmc.ChipGroup(
                    [
                        dmc.Chip(x, value=x, variant="filled", size="xs")
                        for x in [
                            "Correct",
                            "Wrong",
                            "Voicemail",
                        ]
                    ],
                    id={
                        "type": "lead-phone-status",
                        "index": f"{lead.case_id}-{key}",
                    },
                ),
            ]
        )
        for key, phone in lead.phone.items()
    ]
    return dmc.Card(
        children=[
            html.Div(
                hidden=True,
                id={"type": "lead-output-id", "index": lead.case_id},
            ),
            dmc.CardSection(
                dmc.Group(
                    children=[
                        dmc.Text(
                            f"{lead.first_name} {lead.middle_name} {lead.last_name}",
                            weight=500,
                        ),
                        dmc.ActionIcon(
                            DashIconify(
                                icon="material-symbols:supervised-user-circle-outline"
                            ),
                            color="gray",
                            variant="transparent",
                        ),
                    ],
                    position="apart",
                ),
                withBorder=True,
                inheritPadding=True,
                py="xs",
            ),
            dmc.Group(
                [
                    dmc.Text(f"Case#{lead.case_id}", weight=500),
                    html.Div(hidden=True, children=lead.case_id, id="case-id"),
                    dmc.Badge(
                        lead.status.capitalize(),
                        variant="light",
                    ),
                ],
                position="apart",
                mt="md",
                mb="xs",
            ),
            dmc.Divider(variant="solid", className="mt-2"),
            create_group_item(
                label="Name",
                value=f"{lead.first_name} {lead.middle_name} {lead.last_name}",
                icon="material-symbols:supervised-user-circle-outline",
            ),
            create_group_item(
                label="Age",
                value=f"{lead.age}",
                icon="ps:birthday",
            ),
            create_group_item(
                label="Case Date",
                value=f"{lead.case_date:%B %d, %Y}",
                icon="radix-icons:calendar",
            ),
            dmc.Divider(variant="solid", className="mt-2"),
            dmc.Title("→ Charges", order=5, className="mt-3"),
            html.Div(lead.charges_description),
            dmc.Divider(variant="solid", className="mt-2"),
            dmc.Title("→ Notes", order=5, className="mt-3"),
            dmc.Textarea(
                placeholder="Enter notes here...",
                value=lead.notes,
                className="mt-2",
                id={
                    "type": "notes",
                    "index": lead.case_id,
                },
            ),
            html.Div(phones),
            dmc.Divider(variant="solid", className="mt-2 mb-2"),
            dmc.Group(
                [
                    dmc.Button(
                        "Won",
                        id={
                            "type": "won-button",
                            "index": lead.case_id,
                        },
                        leftIcon=DashIconify(icon="healthicons:yes"),
                        color="green",
                        variant="outline",
                    ),
                    dmc.Button(
                        "Lost",
                        leftIcon=DashIconify(icon="healthicons:no"),
                        color="red",
                        variant="outline",
                        id={
                            "type": "lost-button",
                            "index": lead.case_id,
                        },
                    ),
                    dmc.Button(
                        "Wait",
                        leftIcon=DashIconify(icon="solar:menu-dots-broken"),
                        color="yellow",
                        variant="outline",
                        id={
                            "type": "wait-button",
                            "index": lead.case_id,
                        },
                    ),
                ],
                className="mt-2",
                position="center",
            ),
        ],
        withBorder=True,
        shadow="sm",
        radius="md",
        style={"width": 350},
    )