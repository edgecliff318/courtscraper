import logging

import dash_bootstrap_components as dbc
from dash import Dash
from flask_cors import CORS

import src.callbacks as callbacks  # noqa
from src.core.auth import AdvancedAuth
from src.core.config import get_settings
from src.layout.horizontal import Layout
from src.routes.routing import add_routes

settings = get_settings()


def set_logging(app, logging_level):
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    if app.logger.hasHandlers():
        for handler in app.logger.handlers:
            handler.setFormatter(formatter)
            handler.setLevel(logging_level)


def init_app():
    app = Dash(
        meta_tags=[
            {
                "name": "viewport",
                "content": "width=device-width, initial-scale=1",
            }
        ],
        use_pages=True,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        pages_folder="src/pages",
        external_scripts=[
            {
                "src": (
                    "https://cdnjs.cloudflare.com/ajax/libs/",
                    "html2canvas/1.4.0/html2canvas.min.js",
                )
            },
            {
                "src": (
                    "https://cdnjs.cloudflare.com/ajax/libs/"
                    "html2pdf.js/0.10.1/html2pdf.bundle.min.js"
                )
            },
        ],
        assets_folder="src/assets",
        suppress_callback_exceptions=True,
    )

    # Set the app title
    app.title = settings.PROJECT_NAME

    # Set the layout
    app.layout = Layout().render()

    # Set the server
    server = app.server

    # Set logging
    filehandler = logging.FileHandler("app.log")

    app.logger.addHandler(filehandler)
    set_logging(app, settings.LOGGING_LEVEL)

    # Authentication
    auth = AdvancedAuth(app)

    # Add routes
    add_routes(server)

    # CORS
    CORS(server, resources={r"/*": {"origins": "*"}})

    return app, server, auth


app, server, auth = init_app()

if __name__ == "__main__":
    app.run_server(debug=True, port=3000)
