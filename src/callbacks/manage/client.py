import base64
import logging
from datetime import datetime, timedelta

import dash
import dash_mantine_components as dmc
from dash import ALL, Input, Output, State, callback, dcc, html
import openai

from src.connectors.intercom import IntercomConnector
from src.core.config import get_settings
from src.db import bucket
from src.services import cases, templates, participants

logger = logging.getLogger(__name__)
settings = get_settings()


def upload_to_client(email, subject, message):
    intercom = IntercomConnector(settings.INTERCOM_API_KEY)

    contact = intercom.search_contact(email="shawn@tickettakedown.com")
    admins = intercom.get_admins()

    output = intercom.send_message(
        sender=admins[0],
        contact=contact,
        message=message,
    )

    return output


@callback(
    Output("modal-client-preview-parameters", "children"),
    Input("modal-client-preview", "opened"),
    Input("modal-client-preview-generate", "n_clicks"),
    Input("section-client-select-template", "value"),
    State({"type": "modal-client-pars", "index": ALL}, "value"),
    State("case-id", "children"),
    prevent_initial_call=True,
)
def modal_client_pars(opened, update, template, pars, case_id):
    ctx = dash.callback_context
    if opened is False or opened is None:
        return dash.no_update

    if template is None:
        return "Please select a template", dash.no_update

    template_details = templates.get_single_template(template)

    logger.info(f"Getting the context data for {template}")

    # Generate the email using Open AI
    if ctx.triggered[0]["prop_id"] == "modal-client-preview-generate.n_clicks":
        pass

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
                id={"type": "modal-client-pars", "index": "attachments"},
            ),
            dcc.Upload(
                id={"type": "modal-client-pars", "index": "upload"},
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
                id={"type": "modal-client-pars", "index": "email"},
                value=", ".join(emails_list),
            ),
            dmc.TextInput(
                label="Subject",
                placeholder="Enter the subject",
                id={"type": "modal-client-pars", "index": "subject"},
                value=subject_filled,
            ),
            dmc.Textarea(
                label="Body",
                placeholder="Enter the body",
                id={"type": "modal-client-pars", "index": "body"},
                value=body_filled,
                minRows=20,
            ),
            attachments,
        ]
    )

    return params


@callback(
    Output("modal-client-preview-content", "children"),
    Input("modal-client-preview", "opened"),
    Input({"type": "modal-client-pars", "index": ALL}, "value"),
    Input({"type": "modal-client-pars", "index": "upload"}, "contents"),
    Input({"type": "modal-client-pars", "index": ALL}, "n_clicks"),
    Input("section-client-select-template", "value"),
    State({"type": "modal-client-pars", "index": "upload"}, "filename"),
    State("case-id", "children"),
    prevent_initial_call=True,
)
def modal_client_preview(
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
        '{"index":"attachments","type":"modal-client-pars"}.value', []
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
                                "type": "modal-client-pars",
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
            ctx.inputs.get('{"index":"body","type":"modal-client-pars"}.value')
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
    output=Output("modal-client-response", "children"),
    inputs=[
        Input("modal-client-submit", "n_clicks"),
        State({"type": "modal-client-pars", "index": ALL}, "value"),
        State("case-id", "children"),
        State("section-client-select-template", "value"),
    ],
    running=[
        (Output("modal-client-submit", "disabled"), True, False),
        (Output("modal-client-cancel", "disabled"), False, True),
        (
            Output("modal-client-response", "style"),
            {"visibility": "hidden"},
            {"visibility": "visible"},
        ),
        (
            Output("modal-client-submit", "loading"),
            True,
            False,
        ),
    ],
    cancel=[Input("modal-client-cancel", "n_clicks")],
    prevent_initial_call=True,
    background=False,
)
def modal_client_submit(n_clicks, pars, case_id, template):
    ctx = dash.callback_context
    if ctx.triggered[0]["prop_id"] == "modal-client-submit.n_clicks":
        # Check the event on the case events
        email = ctx.states.get(
            '{"index":"email","type":"modal-client-pars"}.value'
        )

        subject = ctx.states.get(
            '{"index":"subject","type":"modal-client-pars"}.value'
        )

        body = ctx.states.get(
            '{"index":"body","type":"modal-client-pars"}.value'
        )
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
        if event.get("template") in [
            e.get("template") for e in events if e.get("template") is not None
        ]:
            return html.Div(
                [
                    dmc.Alert(
                        "Email already sent to the client",
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
        output = upload_to_client(email=email, subject=subject, message=body)

        # Add the event to the list
        events.append(event)

        # Update the case status
        # TODO: Add a status to the case

        # Upload the event
        cases.patch_case(case_id, {"events": events})

        return html.Div(
            [
                dmc.Alert(
                    "Message successfully sent to the client through Intercom",
                    color="teal",
                    title="Success",
                )
            ]
        )
