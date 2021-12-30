import dash
import logging
import sys

import dash_bootstrap_components as dbc
from core.auth import AdvancedAuth
import config


class DashLogger(logging.StreamHandler):
    def __init__(self, stream=None):
        super().__init__(stream=stream)
        self.logs = list()
        self.name = "DashLogger"

    def emit(self, record):
        try:
            msg = self.format(record)
            self.logs.append(msg)
            self.logs = self.logs[-1000:]
            self.flush()
        except Exception:
            self.handleError(record)


dash_logger = DashLogger(stream=sys.stdout)


def set_logging(app, logging_level):
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if app.logger.hasHandlers():
        for handler in app.logger.handlers:
            handler.setFormatter(formatter)
            handler.setLevel(logging_level)


app = dash.Dash(name="Record Wash", external_stylesheets=[dbc.themes.ZEPHYR],
                **config.pathname_params)

auth = AdvancedAuth(
    app
)

filehandler = logging.FileHandler("app.log")

app.logger.addHandler(dash_logger)
app.logger.addHandler(filehandler)
set_logging(app, config.logging_level)
