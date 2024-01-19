import logging

import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

logger = logging.Logger(__name__)


def get_client_section():
    stack = dmc.Stack(
        children=[
            dmc.Modal(
                children=[
                    dmc.Grid(
                        children=[
                            dmc.Col(
                                html.Div(
                                    dmc.Loader(
                                        color="blue", size="md", variant="dots"
                                    ),
                                    id="modal-client-preview-content",
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
                                                    "type": "modal-client-pars",
                                                    "index": "upload",
                                                },
                                            ),
                                        ],
                                        id="modal-client-preview-parameters",
                                    ),
                                    dmc.Stack(
                                        [
                                            html.Div(
                                                children="Please review the email and the attachments and click on the 'Submit to client' button to submit the document to the client.",
                                                id="modal-client-response",
                                                className="mt-2",
                                            ),
                                        ]
                                    ),
                                    dmc.Group(
                                        [
                                            dmc.Button(
                                                "Generate using AI",
                                                id="modal-client-preview-generate",
                                                className="m-2",
                                                leftIcon=DashIconify(
                                                    icon="fluent:database-plug-connected-20-filled"
                                                ),
                                                variant="filled",
                                                color="dark",
                                            ),
                                            dmc.Button(
                                                "Submit to client",
                                                id="modal-client-submit",
                                                className="m-2",
                                                leftIcon=DashIconify(
                                                    icon="formkit:submit"
                                                ),
                                                variant="filled",
                                                color="dark",
                                            ),
                                            dmc.Button(
                                                "Cancel Submission",
                                                id="modal-client-cancel",
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
                title="Preview the Communication",
                id="modal-client-preview",
                size="95%",
                zIndex=10000,
            ),
            dmc.Select(
                label="Document Template",
                icon=DashIconify(icon="radix-icons:magnifying-glass"),
                rightSection=DashIconify(icon="radix-icons:chevron-down"),
                id="section-client-select-template",
            ),
            dmc.Button(
                "Preview & Submit",
                leftIcon=DashIconify(icon="fluent:preview-link-20-filled"),
                id="modal-client-preview-button",
                variant="filled",
                color="dark",
            ),
        ],
        style={"maxWidth": "400px"},
    )

    return stack
