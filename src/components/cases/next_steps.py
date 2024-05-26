import dash_mantine_components as dmc
from dash import html

from src.components.inputs import generate_form_group


def get_next_step_modal_content(
    status_options=None, status_value=None, message=None, send_sms=False
):
    return dmc.Stack(
        [
            dmc.Title("Case Status Update", order=4),
            generate_form_group(
                label="Update the status to:",
                id="modal-next-step-status",
                placeholder="Update the status",
                type="Select",
                options=status_options,
                value=status_value,
                persistence_type="session",
                persistence=True,
            ),
            dmc.Checkbox(
                label="Trigger an SMS Notification to the Client",
                id="modal-next-step-sms",
                checked=False if send_sms is None else send_sms,
                color="dark",
            ),
            generate_form_group(
                label="Write a message to the client",
                id="modal-next-step-message",
                placeholder="Type in the message",
                type="Textarea",
                minRows=10,
                value=message,
            ),
            html.Div(id="modal-next-step-output"),
            dmc.Group(
                [
                    dmc.Button(
                        "Submit",
                        color="dark",
                        id="modal-next-step-submit-button",
                        variant="filled",
                    ),
                    dmc.Button(
                        "Close",
                        color="dark",
                        variant="filled",
                        id="modal-next-step-close-button",
                    ),
                ],
                justify="right",
            ),
        ]
    )


def get_next_step_modal():
    return dmc.Modal(
        id="modal-next-step",
        size="lg",
        zIndex=10000,
        children=get_next_step_modal_content(),
        keepMounted=True,
    )
