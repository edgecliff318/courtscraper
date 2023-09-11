import base64
import logging
from datetime import datetime, timedelta

import dash_mantine_components as dmc
import openai
from dash import dcc, html

from src.core.config import get_settings
from src.db import bucket
from src.services import cases, participants, templates

logger = logging.getLogger(__name__)
settings = get_settings()


def get_email_params(
    template, trigger, case_id, states, inputs, role="client"
):
    template_details = templates.get_single_template(template)

    logger.info(f"Getting the context data for {template}")

    documents = bucket.list_blobs(prefix=f"cases/{case_id}/", delimiter="/")

    # Attachments form

    attachments = dmc.Stack(
        [
            dmc.MultiSelect(
                label="Attachments",
                placeholder="Select the attachments",
                data=[
                    {"label": doc.name, "value": doc.name} for doc in documents
                ],
                value=[],
                id={"type": f"modal-{role}-pars", "index": "attachments"},
            ),
            dcc.Upload(
                id={"type": f"modal-{role}-pars", "index": "upload"},
                children=html.Div(
                    ["Drag and Drop or ", html.A("Select Files")]
                ),
                style={
                    "width": "100%",
                    "height": "60px",
                    "lineHeight": "60px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "10px",
                },
                # Allow multiple files to be uploaded
                multiple=True,
            ),
        ]
    )

    case_data = cases.get_context_data(case_id)

    # Jinja2 template fill in
    subject = template_details.subject
    if subject is None:
        subject = ""
    subject_filled = subject.format_map(case_data)

    body = template_details.text
    if body is None:
        body = ""

    body_filled = body.format_map(case_data)

    # Generate the email using Open AI
    if trigger == f"modal-{role}-preview-generate.n_clicks":
        logger.info("Generating the email using OpenAI")
        openai.api_key = settings.OPENAI_API_KEY

        system_intel = (
            f"You are an attorney and you are writing an email to the {role}"
        )

        system_intel += "\n\n"

        prompt = states.get(
            f'{{"index":"email","type":"modal-{role}-pars"}}.value', ""
        )

        prompt = prompt
        result = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": system_intel},
                {"role": "user", "content": prompt},
            ],
        )

        body_filled = result["choices"][0]["message"]["content"]

    emails_list = []

    # Params should be subject, body (texarea), attachments
    if (
        case_data.get("case_participants") is not None
        and len(case_data.get("case_participants", [])) > 0
    ):
        participants_list = participants.ParticipantsService().get_items(
            id=case_data.get("case_participants", []), role="defendant"
        )

        emails_list = [
            p.email
            for p in participants_list
            if p.email is not None
            for p in participants_list
        ]

    params = dmc.Stack(
        [
            dmc.TextInput(
                label="Email",
                placeholder="Enter the email",
                id={"type": f"modal-{role}-pars", "index": "email"},
                value=", ".join(emails_list),
            ),
            dmc.TextInput(
                label="Subject",
                placeholder="Enter the subject",
                id={"type": f"modal-{role}-pars", "index": "subject"},
                value=subject_filled,
            ),
            dmc.Textarea(
                label="Body",
                placeholder="Enter the body",
                id={"type": f"modal-{role}-pars", "index": "body"},
                value=body_filled,
                minRows=20,
            ),
            attachments,
        ]
    )

    return params


def get_preview(
    template,
    trigger,
    case_id,
    states,
    inputs,
    file_content,
    filename,
    role="client",
):
    logger.info(f"Getting the context data for {template}")
    message = dmc.Text("Email Preview")
    if file_content is not None:
        # Upload the file to the bucket
        for content, name in zip(file_content, filename):
            blob = bucket.blob(f"cases/{case_id}/{name}")
            content_type, content_string = content.split(",")
            decoded = base64.b64decode(content_string)
            blob.upload_from_string(decoded, content_type="application/pdf")

        message = dmc.Alert(
            "File uploaded successfully. Please select the file in the attachments list.",
            color="green",
            title="Success",
        )

    # Generate the HTML preview
    attachments = inputs.get(
        f'{{"index":"attachments","type":"modal-{role}-pars"}}.value', []
    )

    if attachments:
        attachment_stack = dmc.Stack(
            [
                dmc.Group(
                    [
                        dmc.Text(f"Attachment: {a}"),
                        dmc.Button(
                            "Preview",
                            id={
                                "type": f"modal-{role}-pars",
                                "index": f"preview-{a}",
                            },
                        ),
                    ]
                )
                for a in attachments
            ]
        )
    else:
        attachment_stack = dmc.Text("No attachments")

    # If click on preview-{attachment}, then preview the attachment
    if trigger.startswith('{"index":"preview-'):
        attachment = trigger.split("-")[1]
        attachment = attachment.split('"')[0]
        attachment = attachment.split("/")[-1]

        media_url = bucket.blob(
            f"cases/{case_id}/{attachment}"
        ).generate_signed_url(
            version="v4",
            expiration=datetime.utcnow() + timedelta(minutes=15),
            method="GET",
        )

        preview = html.Iframe(
            src=media_url,
            style={
                "width": "100%",
                "height": "100%",
                "min-height": "600px",
            },
        )

    else:
        preview = html.Div(
            inputs.get(f'{{"index":"body","type":"modal-{role}-pars"}}.value')
        )

    document_preview = dmc.Card(
        children=[
            message,
            dmc.Divider(className="my-4"),
            preview,
            dmc.Divider(className="my-4"),
            attachment_stack,
        ],
        shadow="sm",
    )

    # Put the attachements in a multi select
    # and add a button to upload the attachments

    return document_preview


def send_email(
    template,
    trigger,
    case_id,
    states,
    inputs,
    attachments,
    send_function,
    role="client",
):
    # Check the event on the case events
    email = states.get(f'{{"index":"email","type":"modal-{role}-pars"}}.value')

    subject = states.get(
        f'{{"index":"subject","type":"modal-{role}-pars"}}.value'
    )

    body = states.get(f'{{"index":"body","type":"modal-{role}-pars"}}.value')
    event = {
        "case_id": case_id,
        "template": template,
        "date": datetime.now(),
        "subject": subject,
        "body": body,
        "email": email,
    }

    case_data = cases.get_single_case(case_id)
    events = case_data.events

    # Upload the case to casenet
    if events is None:
        events = []
    # TODO: Remove afterwards
    # events = []
    # If the event is already in the list, raise an error$
    if event.get("template") in [
        e.get("template")
        for e in events
        if e.get("template") is not None and e.get("template") != "custom"
    ]:
        return html.Div(
            [
                dmc.Alert(
                    f"Email already sent to the {role}",
                    color="red",
                    title="Information",
                ),
            ]
        )

    template_details = templates.get_single_template(template)

    if template_details.parameters is None:
        params = {}
    else:
        params = template_details.parameters

    params.setdefault("template_title", template_details.name)

    # Upload the document to the client
    output = send_function(
        email=email, subject=subject, message=body, attachments=attachments
    )

    event["details"] = output

    # Add the event to the list
    events.append(event)

    # Update the case status
    # TODO: Add a status to the case

    # Upload the event
    cases.patch_case(case_id, {"events": events})

    return html.Div(
        [
            dmc.Alert(
                f"Message successfully sent to the {role} through Intercom",
                color="teal",
                title="Success",
            )
        ]
    )
