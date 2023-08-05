import logging

import dash
from dash import Input, Output, State, callback

from src.services import cases

logger = logging.Logger(__name__)


@callback(
    Output("modal-court-preview-content", "children"),
    Input("modal-court-preview", "opened"),
    State("case-select-id", "value"),
)
def modal_court_preview(opened, case_id):
    # Generate the document

    # Generate the preview

    # Add control buttons to validate or cancel

    # Add a download button and an upload button

    pass


@callback(
    Output("modal-court-submit-content", "children"),
    Input("modal-court-submit", "opened"),
    State("case-select-id", "value"),
)
def modal_court_submit(opened, case_id):
    # Retrieve the generated document

    # If not generated, display a message and generate it

    # Add control buttons to validate or cancel

    # Add status on the upload to case net

    # Update the case after the upload

    pass
