from app import app
import os

import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

import config
from loader.tickets import TicketsManager


@app.callback(
    Output("file-list", "children"),
    [Input("upload-data", "filename"), Input("upload-data", "contents")],
)
def update_output(uploaded_filenames, uploaded_file_contents):
    """Save uploaded files and regenerate the file list."""
    ticket_manager = TicketsManager(folder_path=config.upload_path)
    if uploaded_filenames is not None and uploaded_file_contents is not None:
        for name, data in zip(uploaded_filenames, uploaded_file_contents):
            ticket_manager.save(name, data)

    files = ticket_manager.list()
    if len(files) == 0:
        return [html.Li("No files yet!")]
    else:
        list_group = dbc.ListGroup(
            [
                dbc.ListGroupItem(
                    filename,
                    href=f"/process/{filename}"
                ) for filename in files
            ]
        )
        return list_group
