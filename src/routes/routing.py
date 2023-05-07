import os

from flask import flash, redirect, request, send_from_directory
from werkzeug.utils import secure_filename

from src.core.config import get_settings

settings = get_settings()


def add_routes(server):
    @server.route("/download/<path:path>")
    def download(path):
        """Serve a file from the upload directory."""
        return send_from_directory(
            settings.UPLOAD_PATH, path, as_attachment=True
        )

    @server.route("/documents/<path:path>")
    def documents(path):
        """Serve a file from the upload directory."""
        return send_from_directory(
            settings.OUTPUT_PATH, path, as_attachment=True
        )

    @server.route(
        "/images/<path:image>",
        methods=["GET"],
    )
    def images(image):
        """Serve a file from the upload directory."""
        api_key = request.args.get("api_key")
        if api_key != settings.API_KEY:
            return "API Key Not Correct"
        image = image.replace("/", "")
        return send_from_directory(
            settings.DATA_PATH, image, as_attachment=False
        )

    UPLOAD_DATA_FOLDER = settings.DATA_PATH

    @server.route("/upload", methods=["POST"])
    def upload_file():
        api_key = request.args.get("api_key")
        if api_key != settings.API_KEY:
            return "API Key Not Correct"
        if request.method == "POST":
            # check if the post request has the file part
            if "file" not in request.files:
                flash("No file part")
                return redirect(request.url)
            file = request.files["file"]
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == "":
                flash("No selected file")
                return redirect(request.url)
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_DATA_FOLDER, filename))

            return "success"
