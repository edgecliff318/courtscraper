import uuid
import os
from dash import dcc
from dash import html

from flask import send_from_directory, Flask, flash, request, redirect, url_for
from flask_cors import CORS
import requests
from werkzeug.utils import secure_filename

from app import app

from components.layout import layout as main_layout
import config

import callbacks
from loader.leads import LeadsLoader

session_id = str(uuid.uuid4())

app.layout = main_layout

server = app.server

CORS(server, resources={r"/*": {"origins": "*"}})


@server.route("/download/<path:path>")
def download(path):
    """Serve a file from the upload directory."""
    return send_from_directory(config.upload_path, path, as_attachment=True)


@server.route("/documents/<path:path>")
def documents(path):
    """Serve a file from the upload directory."""
    return send_from_directory(config.output_path, path, as_attachment=True)


UPLOAD_CACHE_FOLDER = './temp'
UPLOAD_DATA_FOLDER = './data'


@server.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        filename = secure_filename(file.filename)
        if request.args.get("cache", "true").lower() == "true":
            file.save(os.path.join(UPLOAD_CACHE_FOLDER, filename))
        else:
            file.save(os.path.join(UPLOAD_DATA_FOLDER, filename))

        return "success"


@server.route('/update', methods=['POST'])
def update_data():
    if request.method == 'POST':
        data = request.json
        lead_loader = LeadsLoader(
            path=os.path.join(config.config_path, "leads.json")
        )
        leads = lead_loader.load()
        lead = leads.get(data.get("case_id"), {})
        lead.update(data)
        leads[data.get("case_id")] = lead
        lead_loader.save(leads)
        return "success"


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
