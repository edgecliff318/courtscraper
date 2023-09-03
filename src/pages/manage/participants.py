import logging

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from src.components.edits import render_edit_component
from src.models.participants import Participant
from src.services.participants import ParticipantsService

logger = logging.Logger(__name__)

dash.register_page(
    __name__, order=5, path_template="/manage/participants/<participant_id>"
)


def layout(participant_id):
    fields = []

    fields += [
        {
            "id": "role",
            "type": "Select",
            "placeholder": "Role",
            "options": [
                {"label": "Defendant", "value": "defendant"},
                {"label": "Prosecutor", "value": "prosecutor"},
                {"label": "Judge", "value": "judge"},
                {"label": "Lawyer", "value": "lawyer"},
                {"label": "Witness", "value": "witness"},
                {"label": "Other", "value": "other"},
            ],
        }
    ]
    fields += [
        {
            "id": key,
            "type": "Input",
            "placeholder": key,
            "value": value.default,
        }
        for key, value in Participant.model_fields.items()
        if key not in ["id", "role"]
    ]

    participants_search = dbc.Row(
        [
            dbc.Col(
                dmc.Paper(
                    dmc.Select(
                        label="Participants",
                        placeholder="Select participants",
                        searchable=True,
                        description="You can select the case participants here. ",
                        id="participants-list",
                    ),
                    shadow="xs",
                    p="md",
                    radius="md",
                ),
                width=12,
                class_name="mb-2",
            )
        ]
    )
    if (
        participant_id is None
        or participant_id == "#"
        or participant_id == "none"
    ):
        return dbc.Row(
            [
                dbc.Col(
                    dmc.Paper(
                        [
                            participants_search,
                            render_edit_component(
                                fields, "participants", participant_id
                            ),
                        ],
                        shadow="xs",
                        p="md",
                        radius="md",
                    ),
                    width=12,
                    class_name="mb-2",
                ),
            ]
        )

    participants_service = ParticipantsService()

    participant = participants_service.get_single_item(participant_id)

    if participant is None:
        return dbc.Row(
            [
                dbc.Col(
                    dmc.Paper(
                        children=[
                            dmc.Alert(
                                (
                                    "Participant not found. Please get in"
                                    " touch with the technical support"
                                ),
                                color="red",
                            ),
                        ],
                        shadow="xs",
                        p="md",
                        radius="md",
                    ),
                    width=12,
                ),
                participants_search,
            ]
        )

    for field in fields:
        field["value"] = getattr(participant, field["id"])

    return dbc.Row(
        [
            dbc.Col(
                dmc.Paper(
                    [
                        participants_search,
                        render_edit_component(
                            fields, "participants", participant_id
                        ),
                    ],
                    shadow="xs",
                    p="md",
                    radius="md",
                ),
                width=12,
                class_name="mb-2",
            ),
        ]
    )
