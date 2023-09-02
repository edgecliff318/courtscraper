import dash_mantine_components as dmc
from src.models.cases import Case
from src.services.participants import get_participants
from dash_iconify import DashIconify
from dash import html


def get_participants_section(case):
    participants = case.participants

    participants_all = get_participants()

    participants_data = [
        {"label": f"{p.role}{p.first_name} {p.last_name}", "value": p.id}
        for p in participants_all
    ]

    participants_select = dmc.MultiSelect(
        data=participants_data,
        label="Participants",
        placeholder="Select participants",
        value=participants,
    )

    # Selected participants using badges

    participants_selected = []
    if participants is not None:
        participants_selected = [
            dmc.Badge(
                f"{p.role} - {p.first_name} {p.last_name}",
                color="blue",
                variant="filled",
                sx={"margin": "0.25rem"},
            )
            for p in participants_all
            if p.id in participants
        ]

    return participants_select, participants_selected


def get_case_details(case: Case):
    # Screen to display the details of a case and enable editing
    participants_select, participants_selected = get_participants_section(case)

    sections = dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Button(
                        "Save",
                        color="indigo",
                        id="case-manage-save",
                        leftIcon=DashIconify(icon="material-symbols:save"),
                    ),
                    dmc.Button(
                        "Sync with Casenet",
                        color="indigo",
                        id="case-manage-refresh",
                        leftIcon=DashIconify(icon="material-symbols:save"),
                    ),
                    dmc.Button(
                        "Insert Participants from Case",
                        color="indigo",
                        id="case-manage-insert-participants",
                        leftIcon=DashIconify(icon="mdi:arrow-up-bold"),
                    ),
                ],
                position="right",
            ),
            html.Div(id="case-manage-save-output"),
            html.Div(id="case-manage-insert-participants-output"),
            dmc.Divider(),
            participants_select,
            participants_selected,
            dmc.Divider(),
        ],
        className="mt-2",
    )

    return sections
