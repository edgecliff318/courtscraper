import base64
import logging
from datetime import datetime, timedelta

import dash_mantine_components as dmc
import openai
from dash import dcc, html
from flask import session

from src.components.cases.payments import get_invoice_widget
from src.connectors import payments as payments_connector
from src.core.config import get_settings
from src.db import bucket
from src.services import cases, participants
from src.services import settings as settings_service
from src.services import templates

logger = logging.getLogger(__name__)
settings = get_settings()


def get_invoice_text(invoices):
    invoice_text = None
    if invoices is not None and invoices:
        invoice_text = []
        # Generate link
        payments_service = payments_connector.PaymentService()
        for invoice in invoices:
            invoice_data = payments_service.get_invoice(invoice)
            invoice_link = invoice_data.hosted_invoice_url
            invoice_amount = invoice_data.amount_due / 100
            invoice_message = f"<a href='{invoice_link}'>Invoice</a>"

            invoice_text.append(invoice_message)

        invoice_text = "<br>".join(invoice_text)

    return invoice_text


def update_email_text(email_text, invoice_text):
    if email_text is None:
        return email_text
    if invoice_text is None and "{{invoice}}" in email_text:
        raise ValueError(
            "Please select an invoice as the email contains the invoice text but no invoice was selected",
        )

    if invoice_text is not None:
        if "{{invoice}}" not in email_text:
            raise ValueError(
                "Please add {{invoice}} to the email body to add the invoice link that you selected",
            )
        email_text = email_text.replace("{{invoice}}", invoice_text)

    return email_text


def get_email_params(
    template,
    trigger,
    case_id,
    states,
    inputs,
    role="client",
    include_invoice=True,
):
    template_details = templates.get_single_template(template)

    logger.info(f"Getting the context data for {template}")

    documents = get_documents(case_id)

    # Attachments form
    attachments = dmc.Stack(
        [
            dmc.MultiSelect(
                label="Attachments",
                placeholder="Select the attachments",
                data=documents,
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

    # Params should be subject, body (texarea), attachments
    emails_list = []
    participants_list = []
    if (
        case_data.get("case_participants") is not None
        and len(case_data.get("case_participants", [])) > 0
    ):
        participants_list = participants.ParticipantsService().get_items(
            id=case_data.get("case_participants", []),
            role="defendant" if role == "client" else role,
        )

        emails_list = [
            p.email
            for p in participants_list
            if p.email is not None
            for p in participants_list
        ]

        participant_names = [
            p.first_name for p in participants_list if p.first_name is not None
        ]
        # Add the participants and capitalise the first letter
        case_data["participant_name"] = ", ".join(
            [p.capitalize() for p in participant_names]
        )

    # Invoice form
    invoice_widget = html.Div()
    if include_invoice:
        invoice_widget = get_invoice_widget(participants_list, role=role)

    # Get the signature from the settings
    user_email = session.get("profile", {}).get("name", None)
    user_settings = settings_service.UserSettingsService().get_single_item(
        user_email
    )

    if user_settings is not None:
        case_data["signature"] = user_settings.signature

    # Jinja2 template fill in
    subject = template_details.subject
    if subject is None:
        subject = ""
    subject_filled = subject.format_map(case_data)

    body = template_details.text
    if body is None:
        body = ""

    try:
        body_filled = body.format_map(case_data)
        # Replace \\n with \n
        body_filled = body_filled.replace("\\n", "\n")
    except Exception as e:
        logger.error(f"Error filling in the template: {e}")
        body_filled = body

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
                autosize=True,
            ),
            dmc.Text(
                "Use <strong> text </strong> to bold the text", size="xs"
            ),
            dmc.Text(
                "Use {{invoice}} to place the invoice link and text",
                size="xs",
            ),
            html.A(
                dmc.Text(
                    "See all the possible formatting options here", size="xs"
                ),
                href="https://www.w3schools.com/html/html_formatting.asp",
                target="_blank",
            ),
            attachments,
            invoice_widget,
        ]
    )

    return params


def get_documents(case_id):
    case = cases.get_single_case(case_id)
    document_blobs = bucket.list_blobs(
        prefix=f"cases/{case_id}/", delimiter="/"
    )

    # Get casenet documents and if not in the list, add them
    if case.documents is not None:
        for document in case.documents:
            try:
                file_path = document.get("file_path")
                if file_path:
                    if file_path not in [blob.name for blob in document_blobs]:
                        # Copy the file from the current path to the new path
                        blob = bucket.blob(file_path)
                        bucket.copy_blob(
                            blob, bucket, f"cases/{case_id}/{file_path}"
                        )
            except Exception as e:
                logger.error(f"Error copying the file: {e}")

    # Reload the list of documents
    document_blobs = bucket.list_blobs(
        prefix=f"cases/{case_id}/", delimiter="/"
    )
    documents = []
    for blob in document_blobs:
        source = "Uploaded/Generated"
        file_path = blob.name
        if case.documents is not None:
            case_document = case.documents[0]
            case_path = case_document.get("file_path")
            if case_path:
                case_path = case_path.replace("?", "_")
            if case_path in file_path:
                source = case_document.get("source", "Casenet")
                documents.append(
                    {
                        "label": f"{file_path.split('/')[-1]} ({source})",
                        "value": file_path,
                    }
                )
            else:
                documents.append(
                    {
                        "label": f"{file_path.split('/')[-1]} ({source})",
                        "value": file_path,
                    }
                )
        else:
            documents.append(
                {
                    "label": f"{file_path.split('/')[-1]} ({source})",
                    "value": file_path,
                }
            )

    return documents


def get_preview(
    template,
    trigger,
    case_id,
    states,
    inputs,
    file_content,
    filename,
    role="client",
    include_invoice=False,
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
                            variant="filled",
                            color="dark",
                        ),
                    ]
                )
                for a in attachments
            ]
        )
    else:
        attachment_stack = dmc.Text("No attachments")

    # If invoices added
    invoice_text = None
    if include_invoice:
        invoices = inputs.get(
            f'{{"index":"invoices","type":"modal-{role}-pars"}}.value', []
        )
        invoice_text = get_invoice_text(invoices)

    # If click on preview-{attachment}, then preview the attachment
    if isinstance(trigger, dict) and trigger.get("index", "").startswith(
        "preview-"
    ):
        attachment = trigger.get("index", "").split("/")[-1]

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
        email_text = inputs.get(
            f'{{"index":"body","type":"modal-{role}-pars"}}.value'
        )

        try:
            email_text = update_email_text(email_text, invoice_text)

        except ValueError as e:
            message = dmc.Alert(
                f"Error generating the email: {e}",
                color="red",
                title="Error",
            )

        preview = html.Div(email_text)

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
    include_invoice=False,
    force_send=False,
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

    # If the event is already in the list, raise an error$
    template_details = templates.get_single_template(template)
    if (
        not template_details.repeat
        and event.get("template")
        in [e.get("template") for e in events if e.get("template") is not None]
    ) and not force_send:
        return False, html.Div(
            [
                dmc.Alert(
                    f"Email already sent to the {role}",
                    color="red",
                    title="Information",
                ),
            ]
        )

    if template_details.parameters is None:
        params = {}
    else:
        params = template_details.parameters

    params.setdefault("template_title", template_details.name)

    if include_invoice:
        invoices = states.get(
            f'{{"index":"invoices","type":"modal-{role}-pars"}}.value', []
        )
        invoice_text = get_invoice_text(invoices)
        body = update_email_text(body, invoice_text)

    # Upload the document to the client
    try:
        output = send_function(
            email=email,
            subject=subject,
            message=body,
            attachments=attachments,
            case_id=case_id,
        )
    except Exception as e:
        logger.error(f"Error sending the email: {e}")
        return False, html.Div(
            [
                dmc.Alert(
                    f"Error sending the email: {e}",
                    color="red",
                    title="Error",
                ),
            ]
        )

    event["details"] = output

    # Add the event to the list
    events.append(event)

    # Update the case status
    # TODO: Add a status to the case

    # Upload the event
    cases.patch_case(case_id, {"events": events})

    event["template"] = template_details

    return event, html.Div(
        [
            dmc.Alert(
                f"Message successfully sent to the {role}",
                color="teal",
                title="Success",
            )
        ]
    )
