import base64
import logging

import dash_mantine_components as dmc
from dash import Input, Output, State, callback

from src.core.config import get_settings
from src.db import bucket

logger = logging.getLogger(__name__)
settings = get_settings()


@callback(
    Output("document-upload-status", "children"),
    Input("documents-upload", "contents"),
    State("documents-upload", "filename"),
    State("case-id", "children"),
    prevent_initial_call=True,
)
def upload_from_attachment(file_content, filename, case_id):
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
        return message
