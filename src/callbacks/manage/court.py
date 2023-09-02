import logging
from collections.abc import MutableMapping
from datetime import datetime, timedelta

import dash
import dash_mantine_components as dmc
from dash import ALL, Input, Output, State, callback, html
from dash_iconify import DashIconify
from google.cloud.storage.retry import DEFAULT_RETRY

from src.connectors.casenet import CaseNetWebConnector
from src.core.config import get_settings
from src.core.document import DocumentGenerator, convert_doc_to_pdf
from src.db import bucket
from src.services import cases, templates

logger = logging.getLogger(__name__)
settings = get_settings()


def flatten(dictionary, parent_key="", separator="_"):
    items = []
    for key, value in dictionary.items():
        new_key = parent_key + separator + key if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(flatten(value, new_key, separator=separator).items())
        else:
            items.append((new_key, value))
    return dict(items)


def init_document_generator(case_id, template):
    # Generate the document
    template_filepath = settings.DATA_PATH.joinpath(
        f"{case_id}_{template}.docx"
    )

    # Ensure the folder exists
    logger.info(f"Creating the folder {template_filepath.parent}")
    template_filepath.parent.mkdir(parents=True, exist_ok=True)

    templates.get_template_file(template, template_filepath)

    output_filepath = settings.DATA_PATH.joinpath(
        f"{case_id}_{template}_filled.docx"
    )

    # Generate the preview
    logger.info(f"Initializing the document generator")
    document_generator = DocumentGenerator(
        input_file=template_filepath,
        output_file=output_filepath,
    )

    return document_generator


def get_context_data(case_id, template):
    document_generator = init_document_generator(case_id, template)

    # Add control buttons to validate or cancel
    logger.info(f"Getting the context data for {template}")
    context = document_generator.get_context()

    # Creating the data dictionary
    data = {}

    # Filling the data dictionary with cases data
    logger.info(f"Getting the case data for {case_id}")
    case_data = cases.get_single_case(case_id).model_dump()

    case_data = flatten(case_data)

    # Transform case location
    if "municipal" in case_data.get("location", "").lower():
        case_data["city"] = (
            case_data.get("location", "")
            .lower()
            .replace("municipal", "")
            .upper()
        )
        case_data["city"] += " CITY<"
        case_data["location"] = "MUNICIPAL"
    elif "circuit" in case_data.get("location", "").lower():
        case_data["city"] = (
            case_data.get("location", "")
            .lower()
            .replace("circuit", "")
            .upper()
        )
        case_data["city"] += " COUNTY"
        case_data["location"] = "CIRCUIT"

    data.update({f"case_{key}": value for key, value in case_data.items()})

    # Adding the current date short
    data["current_date_short"] = datetime.now().strftime("%B %d, %Y").upper()

    # Get dash inputs and update the context
    context_data = {k: data.get(k) for k in context}

    logger.info("Finished building data")
    logger.debug(context_data)
    return context_data


def generate_document(case_id, template, context_data):
    logger.info(f"Generating the document for {template}")
    document_generator = init_document_generator(case_id, template)

    document_generator.generate(context_data)

    # Convert the document to PDF
    logger.info("Converting the document to PDF")
    output_filepath_pdf = convert_doc_to_pdf(document_generator.output_file)

    # Upload the PDF to the bucket
    logger.info("Uploading the PDF to the bucket")
    blob = bucket.blob(f"tmp/{case_id}_{template}_filled.pdf")
    blob.upload_from_filename(output_filepath_pdf)
    media_url = blob.generate_signed_url(expiration=timedelta(seconds=3600))

    return media_url, output_filepath_pdf


def upload_to_court(case_id, template, court_location, params=None):
    # Download the PDF from the bucket
    blob = bucket.blob(f"tmp/{case_id}_{template}_filled.pdf")

    # PDF File:
    output_filepath_pdf = settings.DATA_PATH.joinpath(
        f"{case_id}_{template}_filled.pdf"
    )

    modified_retry = DEFAULT_RETRY.with_delay(
        initial=1.5, multiplier=1.2, maximum=45.0
    )

    blob.download_to_filename(
        output_filepath_pdf, retry=modified_retry, timeout=20
    )

    # By Court
    connector = CaseNetWebConnector(params=params)

    # Abs path of the PosixPath
    output_filepath_pdf = str(output_filepath_pdf)

    try:
        connector.submit_document(
            filepath_document=output_filepath_pdf,
            case_number=case_id,
            court_location=court_location,
        )
    except Exception as e:
        logger.error(e)
        raise e
    finally:
        connector.teardown()


def submit_document(case_id, template):
    # PDF File:
    output_filepath_pdf = settings.DATA_PATH.joinpath(
        f"{case_id}_{template}_filled.pdf"
    )

    firestore_filepath_pdf = f"cases/{case_id}/{template}.pdf"
    # Download the PDF from the bucket
    blob = bucket.blob(f"tmp/{case_id}_{template}_filled.pdf")
    modified_retry = DEFAULT_RETRY.with_delay(
        initial=1.5, multiplier=1.2, maximum=45.0
    )
    blob.download_to_filename(
        output_filepath_pdf, timeout=20, retry=modified_retry
    )

    # Save the document to the official case folder
    blob = bucket.blob(firestore_filepath_pdf)
    blob.upload_from_filename(output_filepath_pdf)

    return firestore_filepath_pdf


@callback(
    Output("modal-court-preview-content", "children"),
    Output("modal-court-preview-parameters", "children"),
    Input("modal-court-preview", "opened"),
    Input("modal-court-preview-update", "n_clicks"),
    Input("section-court-select-template", "value"),
    State({"type": "modal-court-pars", "index": ALL}, "value"),
    State("case-id", "children"),
    prevent_initial_call=True,
)
def modal_court_preview(opened, update, template, pars, case_id):
    ctx = dash.callback_context
    if opened is False or opened is None:
        return dash.no_update

    if template is None:
        return "Please select a template", dash.no_update

    logger.info(f"Getting the context data for {template}")

    context_data = get_context_data(case_id, template)

    if ctx.triggered[0]["prop_id"] == "modal-court-preview-update.n_clicks":
        for k, v in zip(context_data.keys(), pars):
            context_data[k] = v

    media_url, output_filepath_pdf = generate_document(
        case_id, template, context_data
    )

    # Add a download button and an upload button
    params = dmc.Stack(
        [
            dmc.TextInput(
                label=k.replace("_", " ").title(),
                id={"type": "modal-court-pars", "index": k},
                value=v,
            )
            for k, v in context_data.items()
        ]
    )

    document_preview = dmc.Card(
        children=[
            html.Iframe(
                src=media_url,
                style={
                    "width": "100%",
                    "height": "100%",
                    "min-height": "600px",
                },
            ),
            html.A(
                dmc.Button(
                    "Download",
                    variant="outline",
                    leftIcon=DashIconify(icon="mdi:download"),
                ),
                href=media_url,
            ),
        ],
        shadow="sm",
    )

    return document_preview, params


@callback(
    output=Output("modal-court-response", "children"),
    inputs=[
        Input("modal-court-submit", "n_clicks"),
        State("case-id", "children"),
        State("section-court-select-template", "value"),
    ],
    running=[
        (Output("modal-court-submit", "disabled"), True, False),
        (Output("modal-court-cancel", "disabled"), False, True),
        (
            Output("modal-court-response", "style"),
            {"visibility": "hidden"},
            {"visibility": "visible"},
        ),
        (
            Output("modal-court-submit", "loading"),
            True,
            False,
        ),
    ],
    cancel=[Input("modal-court-cancel", "n_clicks")],
    prevent_initial_call=True,
    background=False,
)
def modal_court_submit(n_clicks, case_id, template):
    ctx = dash.callback_context
    if ctx.triggered[0]["prop_id"] == "modal-court-submit.n_clicks":
        # Check the event on the case events
        event = {
            "case_id": case_id,
            "template": template,
            "document": f"cases/{case_id}/{template}.docx",
            "date": datetime.now(),
        }

        case_data = cases.get_single_case(case_id)
        events = case_data.events
        court_location = case_data.locn_code

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
                        "Document already uploaded to the court system",
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

        # Upload the document to the court
        output = upload_to_court(
            case_id,
            template,
            court_location,
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
                    "Document successfully uploaded to the court system",
                    color="teal",
                    title="Success",
                )
            ]
        )
