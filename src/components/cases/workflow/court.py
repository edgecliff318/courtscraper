import logging

import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

logger = logging.Logger(__name__)


def get_court_section():
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
                                    id="modal-court-preview-content",
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
                                                    "type": "modal-court-pars",
                                                    "index": 0,
                                                },
                                            ),
                                        ],
                                        id="modal-court-preview-parameters",
                                    ),
                                    dmc.Stack(
                                        [
                                            html.Div(
                                                children="Please review the document and click on the 'Submit to Court' button to submit the document to the court.",
                                                id="modal-court-response",
                                                className="mt-2",
                                            ),
                                        ]
                                    ),
                                    dmc.Group(
                                        [
                                            dmc.Button(
                                                "Update",
                                                id="modal-court-preview-update",
                                                className="m-2",
                                                leftIcon=DashIconify(
                                                    icon="fluent:database-plug-connected-20-filled"
                                                ),
                                                variant="filled",
                                                color="dark",
                                            ),
                                            dmc.Button(
                                                "Submit to Court",
                                                id="modal-court-submit",
                                                className="m-2",
                                                leftIcon=DashIconify(
                                                    icon="formkit:submit"
                                                ),
                                                variant="filled",
                                                color="dark",
                                            ),
                                            dmc.Button(
                                                "Cancel Submission",
                                                id="modal-court-cancel",
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
                title="Preview the Document",
                id="modal-court-preview",
                size="90%",
                zIndex=10000,
            ),
            dmc.Select(
                label="Document Template",
                icon=DashIconify(icon="radix-icons:magnifying-glass"),
                rightSection=DashIconify(icon="radix-icons:chevron-down"),
                id="section-court-select-template",
                searchable=True,
            ),
            dmc.Button(
                "Preview & Submit to Court",
                leftIcon=DashIconify(icon="fluent:preview-link-20-filled"),
                id="modal-court-preview-button",
                variant="filled",
                color="dark",
            ),
        ],
    )

    return stack
