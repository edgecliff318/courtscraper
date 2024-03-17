import logging

import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

from src.services.participants import ParticipantsService

logger = logging.Logger(__name__)


def get_prosecutor_section(case):
    participants_service = ParticipantsService()

    if case.participants is None or len(case.participants) == 0:
        return dmc.Alert(
            "No participants found ! Please add participants to the case",
            color="red",
            title="No participants found",
        )

    participants_list = participants_service.get_items(
        id=case.participants, role="prosecutor"
    )
    message = dmc.Alert(
        "Select on the email templates to preview and submit the document/request to the prosecutor.",
        color="blue",
        title="Communicate with the prosecutor",
    )
    if len(participants_list) == 0:
        message = dmc.Alert(
            "No prosecutor selected for this case",
            color="red",
            title="No prosecutor found",
        )

    for participant in participants_list:
        if participant.communication_preference is None:
            message = dmc.Alert(
                f"No communication preference found for the prosecutor {participant.last_name}",
                color="red",
                title="No communication preference found",
            )
        else:
            message = dmc.Alert(
                participant.communication_preference,
                color="blue",
                title=f"Process with the prosecutor {participant.last_name}",
            )

    stack = dmc.Stack(
        children=[
            message,
            dmc.Modal(
                children=[
                    dmc.Grid(
                        children=[
                            dmc.Col(
                                html.Div(
                                    dmc.Loader(
                                        color="blue", size="md", variant="dots"
                                    ),
                                    id="modal-prosecutor-preview-content",
                                ),
                                span=6,
                            ),
                            dmc.Col(
                                [
                                    dmc.Stack(
                                        [
                                            dmc.Loader(
                                                color="blue",
                                                size="md",
                                                variant="dots",
                                            ),
                                            dmc.TextInput(
                                                label="Your data:",
                                                error="Enter a valid value",
                                                style={
                                                    "width": 200,
                                                    # Hidden by default
                                                    "display": "none",
                                                },
                                                id={
                                                    "type": "modal-prosecutor-pars",
                                                    "index": "upload",
                                                },
                                            ),
                                        ],
                                        id="modal-prosecutor-preview-parameters",
                                    ),
                                    dmc.Stack(
                                        [
                                            html.Div(
                                                children="Please review the email and the attachments and click on the 'Submit to Prosecutor' button to submit the document to the prosecutor.",
                                                id="modal-prosecutor-response",
                                                className="mt-2",
                                            ),
                                        ]
                                    ),
                                    dmc.Group(
                                        [
                                            dmc.Button(
                                                "Generate using AI",
                                                id="modal-prosecutor-preview-generate",
                                                className="m-2",
                                                leftIcon=DashIconify(
                                                    icon="fluent:database-plug-connected-20-filled"
                                                ),
                                                variant="filled",
                                                color="dark",
                                            ),
                                            dmc.Button(
                                                "Submit to prosecutor",
                                                id="modal-prosecutor-submit",
                                                className="m-2",
                                                leftIcon=DashIconify(
                                                    icon="formkit:submit"
                                                ),
                                                variant="filled",
                                                color="dark",
                                            ),
                                            dmc.Button(
                                                "Cancel Submission",
                                                id="modal-prosecutor-cancel",
                                                className="m-2",
                                                leftIcon=DashIconify(
                                                    icon="fluent:delete-20-filled"
                                                ),
                                                disabled=True,
                                                variant="filled",
                                                color="dark",
                                            ),
                                        ]
                                    ),
                                ],
                                span=6,
                            ),
                        ],
                        gutter="xl",
                        align="stretch",
                    )
                ],
                title="Preview & Submit",
                id="modal-prosecutor-preview",
                size="100%",
                zIndex=10000,
            ),
            dmc.Select(
                label="Email Template",
                icon=DashIconify(icon="radix-icons:magnifying-glass"),
                rightSection=DashIconify(icon="radix-icons:chevron-down"),
                id="section-prosecutor-select-template",
            ),
            dmc.Button(
                "Preview & Submit",
                leftIcon=DashIconify(icon="fluent:preview-link-20-filled"),
                id="modal-prosecutor-preview-button",
                variant="filled",
                color="dark",
            ),
        ],
    )
    return stack
