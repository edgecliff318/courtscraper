import dash_mantine_components as dmc
from src.components.edits import render_edit_component
from src.models.cases import Case
from src.services.participants import ParticipantsService
from dash_iconify import DashIconify
from dash import dcc, html


def get_participants_section(case):
    participants = case.participants
    participants_service = ParticipantsService()

    participants_all = participants_service.get_items()

    participants_data = [
        {"label": f"{p.role} - {p.first_name} {p.last_name}", "value": p.id}
        for p in participants_all
    ]

    participants_select = dmc.MultiSelect(
        data=participants_data,
        label="Participants",
        placeholder="Select participants",
        value=participants,
        searchable=True,
        description="You can select the case participants here. ",
        id="case-manage-participants",
    )

    # Selected participants using badges

    participants_selected = []
    if participants is not None:
        participants_selected = [
            dcc.Link(
                dmc.Button(
                    f"{p.role.capitalize()} - {p.first_name} {p.last_name}",
                    color="blue",
                    variant="light",
                    size="xs",
                    rightIcon=DashIconify(icon="carbon:view"),
                ),
                href=f"/manage/participants/{p.id}",
            )
            for p in participants_all
            if p.id in participants
        ]
    participants_selected = dmc.Group(participants_selected)

    return participants_select, participants_selected


def get_case_edit(case: Case):
    fields = []
    fields += [
        {
            "id": key,
            "type": "Input",
            "placeholder": key,
            "value": value.default,
        }
        for key, value in Case.model_fields.items()
        if key
        in [
            "disposed",
            "court_type",
            "court_date",
            "court_time",
            "court_link",
        ]
    ]
    for field in fields:
        field["value"] = getattr(case, field["id"])
    return render_edit_component(fields, "cases", case.case_id)


def get_case_details(case: Case):
    # Screen to display the details of a case and enable editing
    participants_select, participants_selected = get_participants_section(case)

    sections = dmc.Stack(
        [
            dmc.Group(
                [
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
            dcc.Store("case-details-id", data=case.case_id),
            html.Div(id="case-details-output"),
            dmc.Divider(),
            participants_select,
            participants_selected,
            dmc.Divider(),
            get_case_edit(case),
        ],
        className="mt-2",
    )

    return sections
