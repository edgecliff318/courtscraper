import logging

import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

logger = logging.Logger(__name__)


def get_prosecutor_section():
    stack = dmc.Stack(
        children=[
            dmc.Modal(
                children=[
                    dmc.Grid(
                        children=[
                            dmc.Col(
                                html.Div(
                                    dmc.Loader(color="blue", size="md", variant="dots"),
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
                                            ),
                                            dmc.Button(
                                                "Submit to prosecutor",
                                                id="modal-prosecutor-submit",
                                                className="m-2",
                                                leftIcon=DashIconify(
                                                    icon="formkit:submit"
                                                ),
                                            ),
                                            dmc.Button(
                                                "Cancel Submission",
                                                id="modal-prosecutor-cancel",
                                                className="m-2",
                                                leftIcon=DashIconify(
                                                    icon="fluent:delete-20-filled"
                                                ),
                                                disabled=True,
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
            ),
        ],
        style={"maxWidth": "400px"},
    )
    return stack
