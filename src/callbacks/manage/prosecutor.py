import base64
import logging
from collections.abc import MutableMapping
from datetime import datetime, timedelta

import openai
import dash
import dash_mantine_components as dmc
from dash import ALL, Input, Output, State, callback, dcc, html
from dash_iconify import DashIconify

from src.core.config import get_settings
from src.db import bucket
from src.services import cases, templates, participants

logger = logging.getLogger(__name__)
settings = get_settings()


def upload_to_prosecutor():
    pass


@callback(
    Output("modal-prosecutor-preview-parameters", "children"),
    Input("modal-prosecutor-preview", "opened"),
    Input("modal-prosecutor-preview-generate", "n_clicks"),
    Input("section-prosecutor-select-template", "value"),
    State({"type": "modal-prosecutor-pars", "index": ALL}, "value"),
    State("case-id", "children"),
    prevent_initial_call=True,
)
def modal_prosecutor_pars(opened, update, template, pars, case_id):
    ctx = dash.callback_context
    if opened is False or opened is None:
        return dash.no_update

    if template is None:
        return "Please select a template", dash.no_update

    template_details = templates.get_single_template(template)

    logger.info(f"Getting the context data for {template}")

    documents = bucket.list_blobs(prefix=f"cases/{case_id}/", delimiter="/")

    attachments = dmc.Stack(
        [
            dmc.MultiSelect(
                label="Attachments",
                placeholder="Select the attachments",
                data=[
                    {"label": doc.name, "value": doc.name} for doc in documents
                ],
                value=[],
                id={"type": "modal-prosecutor-pars", "index": "attachments"},
            ),
            dcc.Upload(
                id={"type": "modal-prosecutor-pars", "index": "upload"},
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
    subject_filled = subject.format(**case_data)

    body = template_details.text
    if body is None:
        body = ""

    body_filled = body.format(**case_data)

    # Generate the email using Open AI
    if (
        ctx.triggered[0]["prop_id"]
        == "modal-prosecutor-preview-generate.n_clicks"
    ):
        logger.info("Generating the email using OpenAI")
        openai.api_key = settings.OPENAI_API_KEY

        system_intel = "You are an attorney and you are writing an email to the prosecutor"

        system_intel += "\n\n"

        prompt = ctx.states.get(
            '{"index":"email","type":"modal-prosecutor-pars"}.value', ""
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
            id=case_data.get("case_participants", []), role="prosecutor"
        )

        emails_list = [
            p.email
            for p in participants_list
            if p.email is not None
            for p in participants_list
        ]

    # Params should be subject, body (texarea), attachments

    params = dmc.Stack(
        [
            dmc.TextInput(
                label="Email",
                placeholder="Enter the email",
                id={"type": "modal-prosecutor-pars", "index": "email"},
                value=", ".join(emails_list),
            ),
            dmc.TextInput(
                label="Subject",
                placeholder="Enter the subject",
                id={"type": "modal-prosecutor-pars", "index": "subject"},
                value=subject_filled,
            ),
            dmc.Textarea(
                label="Body",
                placeholder="Enter the body",
                id={"type": "modal-prosecutor-pars", "index": "body"},
                value=body_filled,
                minRows=20,
            ),
            attachments,
        ]
    )

    return params


@callback(
    Output("modal-prosecutor-preview-content", "children"),
    Input("modal-prosecutor-preview", "opened"),
    Input({"type": "modal-prosecutor-pars", "index": ALL}, "value"),
    Input({"type": "modal-prosecutor-pars", "index": "upload"}, "contents"),
    Input({"type": "modal-prosecutor-pars", "index": ALL}, "n_clicks"),
    Input("section-prosecutor-select-template", "value"),
    State({"type": "modal-prosecutor-pars", "index": "upload"}, "filename"),
    State("case-id", "children"),
    prevent_initial_call=True,
)
def modal_prosecutor_preview(
    opened, pars, file_content, clicks, template, filename, case_id
):
    ctx = dash.callback_context
    if opened is False or opened is None:
        return dash.no_update

    if template is None:
        return "Please select a template", dash.no_update

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
    attachments = ctx.inputs.get(
        '{"index":"attachments","type":"modal-prosecutor-pars"}.value', []
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
                                "type": "modal-prosecutor-pars",
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
    if ctx.triggered[0]["prop_id"].startswith('{"index":"preview-'):
        attachment = ctx.triggered[0]["prop_id"].split("-")[1]
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
            ctx.inputs.get(
                '{"index":"body","type":"modal-prosecutor-pars"}.value'
            )
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


@callback(
    output=Output("modal-prosecutor-response", "children"),
    inputs=[
        Input("modal-prosecutor-submit", "n_clicks"),
        State({"type": "modal-prosecutor-pars", "index": ALL}, "value"),
        State("case-id", "children"),
        State("section-prosecutor-select-template", "value"),
    ],
    running=[
        (Output("modal-prosecutor-submit", "disabled"), True, False),
        (Output("modal-prosecutor-cancel", "disabled"), False, True),
        (
            Output("modal-prosecutor-response", "style"),
            {"visibility": "hidden"},
            {"visibility": "visible"},
        ),
        (
            Output("modal-prosecutor-submit", "loading"),
            True,
            False,
        ),
    ],
    cancel=[Input("modal-prosecutor-cancel", "n_clicks")],
    prevent_initial_call=True,
    background=False,
)
def modal_prosecutor_submit(n_clicks, pars, case_id, template):
    ctx = dash.callback_context
    if ctx.triggered[0]["prop_id"] == "modal-prosecutor-submit.n_clicks":
        # Check the event on the case events
        event = {
            "case_id": case_id,
            "template": template,
            "document": f"cases/{case_id}/{template}.docx",
            "date": datetime.now(),
        }

        case_data = cases.get_single_case(case_id)
        events = case_data.events
        prosecutor_location = case_data.locn_code

        # Upload the case to casenet
        if events is None:
            events = []
        # If the event is already in the list, raise an error$
        if event.get("template") in [
            e.get("template") for e in events if e.get("template") is not None
        ]:
            return html.Div(
                [
                    dmc.Alert(
                        "Document already uploaded to the prosecutor system",
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

        # Upload the document to the prosecutor
        output = upload_to_prosecutor(
            case_id,
            template,
            prosecutor_location,
            params=template_details.parameters,
        )

        # Submit the document
        firestore_filepath_pdf = submit_document(case_id, template)

        event["document"] = firestore_filepath_pdf

        # Add the event to the list
        events.append(event)

        # Update the case status
        # TODO: Add a status to the case

        # Upload the event
        cases.patch_case(case_id, {"events": events})

        return html.Div(
            [
                dmc.Alert(
                    "Document successfully uploaded to the prosecutor system",
                    color="teal",
                    title="Success",
                )
            ]
        )
