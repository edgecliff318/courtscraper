import uuid
from dash import dcc
from dash import html

from flask import send_from_directory
from flask_cors import CORS

from app import app

from components.layout import layout as main_layout
import config

import callbacks

server = app.server

CORS(server, resources={r"/*": {"origins": "*"}})

session_id = str(uuid.uuid4())

app.layout = main_layout


@server.route("/download/<path:path>")
def download(path):
    """Serve a file from the upload directory."""
    return send_from_directory(config.upload_path, path, as_attachment=True)

@server.route("/documents/<path:path>")
def documents(path):
    """Serve a file from the upload directory."""
    return send_from_directory(config.output_path, path, as_attachment=True)

# Validation Layout
app.validation_layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Loading(
        id="loading-all",
        type="default",
        children=html.Div(id="loading")
    ),
    html.Div(id='page-content'),
    main_layout,
])


if __name__ == "__main__":
    app.run_server(debug=True, port=8060)
