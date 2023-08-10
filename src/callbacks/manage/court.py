import logging
from datetime import datetime, timedelta

import dash
import dash_mantine_components as dmc
from dash import ALL, Input, Output, State, callback, html
from dash_iconify import DashIconify

from src.core.config import get_settings
from src.core.document import DocumentGenerator, convert_doc_to_pdf
from src.db import bucket
from src.services import cases, templates

logger = logging.Logger(__name__)

settings = get_settings()


@callback(
    Output("modal-court-preview-content", "children"),
    Output("modal-court-preview-parameters", "children"),
    Input("modal-court-preview", "opened"),
    Input("modal-court-preview-update", "n_clicks"),
    Input("modal-court-submit", "n_clicks"),
    Input("section-court-select-template", "value"),
    State({"type": "modal-court-pars", "index": ALL}, "value"),
    State("case-id", "children"),
    prevent_initial_call=True,
)
def modal_court_preview(opened, update, submit, template, pars, case_id):
    ctx = dash.callback_context
    if opened is False or opened is None:
        return dash.no_update

    if template is None:
        return "Please select a template", dash.no_update

    # Generate the document
    template_filepath = settings.DATA_PATH.joinpath(
        f"{case_id}_{template}.docx"
    )

    templates.get_template_file(template, template_filepath)

    output_filepath = settings.DATA_PATH.joinpath(
        f"{case_id}_{template}_filled.docx"
    )

    # Creating the data dictionary
    data = {}

    # Filling the data dictionary with cases data
    case_data = cases.get_single_case(case_id).dict()

    data.update({f"case_{key}": value for key, value in case_data.items()})
    data["current_date_short"] = datetime.now().strftime("%d/%m/%Y")

    # Generate the preview
    document_generator = DocumentGenerator(
        input_file=template_filepath,
        output_file=output_filepath,
    )

    # Add control buttons to validate or cancel
    context = document_generator.get_context()

    # Get dash inputs and update the context
    context_data = {k: data.get(k) for k in context}

    if ctx.triggered[0]["prop_id"] == "modal-court-preview-update.n_clicks":
        for k, v in zip(context_data.keys(), pars):
            context_data[k] = v

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

    # Generate the document
    document_generator.generate(context_data)

    # Convert the document to PDF
    output_filepath_pdf = convert_doc_to_pdf(output_filepath)

    blob = bucket.blob(f"tmp/{case_id}_{template}_filled.pdf")
    blob.upload_from_filename(output_filepath_pdf)
    media_url = blob.generate_signed_url(expiration=timedelta(seconds=3600))

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

    if ctx.triggered[0]["prop_id"] == "modal-court-submit.n_clicks":
        # Save the document
        blob = bucket.blob(f"cases/{case_id}/{template}.docx")
        blob.upload_from_filename(output_filepath_pdf)

        event = {
            "case_id": case_id,
            "template": template,
            "document": f"cases/{case_id}/{template}.docx",
            "date": datetime.now(),
        }

        events = cases.get_single_case(case_id).events

        # Upload the case to casenet

        if events is None:
            events = []

        events.append(event)

        # Upload the event
        cases.patch_case(case_id, {"events": events})

        return (
            html.Div(
                [
                    dmc.Alert(
                        "Document successfully uploaded",
                        color="teal",
                        title="Success",
                    ),
                    document_preview,
                ]
            ),
            dash.no_update,
        )

    return document_preview, params
