import logging
from email import message

import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

from src.loader.mycase import MyCase
from src.services.participants import ParticipantsService

logger = logging.Logger(__name__)


def get_client_section(case):
    participants_service = ParticipantsService()

    if case.participants is None or len(case.participants) == 0:
        return dmc.Alert(
            "No participants found ! Please add participants to the case",
            color="red",
            title="No participants found",
        )

    participants_list = participants_service.get_items(
        id=case.participants, role="defendant"
    )

    if len(participants_list) == 0:
        return dmc.Alert(
            "No defendant selected for this case",
            color="red",
            title="No participants found",
        )

    for participant in participants_list:
        if participant.mycase_id is None or participant.mycase_id == "None":
            mycase = MyCase(url="", password="", username="")
            mycase.login()
            mycase_details = mycase.search_case(
                case_id=case.case_id,
            )
            client_id = None
            message = None

            if mycase_details is not None:
                clients = mycase_details.get("clients")
            else:
                clients = None

            if clients is None or len(clients) == 0:
                message = dmc.Alert(
                    f"No client found in MyCase with case id {case.case_id}. Please add the client to MyCase and update the participant details.",
                    color="red",
                    title="No client found",
                )
            else:
                client_id = clients[0]["id"]

            if client_id is None and message is None:
                message = dmc.Alert(
                    f"No client found in MyCase with first name {participant.first_name}, last name {participant.last_name} and email {participant.email}. Please add the client to MyCase and update the participant details.",
                    color="red",
                    title="No client found",
                )
            if client_id is not None:
                participant.mycase_id = client_id
                if participant.email is None:
                    participant.email = clients[0]["email"]
                if participant.phone is None or participant.phone == "":
                    participant.phone = clients[0]["phone"]
                participants_service.patch_item(
                    participant.id, {"mycase_id": client_id}
                )
        customer_mycase_button = dmc.Button(
            "Open in MyCase",
            leftIcon=DashIconify(icon="fluent:open-folder-20-filled"),
            id="modal-client-preview-mycase",
            variant="filled",
            color="dark",
            size="xs",
            mt="xs",
        )
        if message is None:
            message = dmc.Alert(
                [
                    dmc.Text(
                        "Select on the email templates to preview and submit the document/request to the client."
                    ),
                    html.A(
                        customer_mycase_button,
                        href=f"https://meyer-attorney-services.mycase.com/contacts/clients/{participant.mycase_id}",
                        target="_blank",
                    ),
                ],
                color="blue",
                title="Communicate with the client",
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
                                            # Using normal emails
                                            dmc.Checkbox(
                                                label="Send email",
                                                id="modal-client-send-email",
                                                checked=(
                                                    True
                                                    if client_id is None
                                                    else False
                                                ),
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
                searchable=True,
            ),
            dmc.Button(
                "Preview & Submit",
                leftIcon=DashIconify(icon="fluent:preview-link-20-filled"),
                id="modal-client-preview-button",
                variant="filled",
                color="dark",
            ),
        ],
    )

    return stack
