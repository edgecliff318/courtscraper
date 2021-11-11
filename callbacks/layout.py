import os
import dash.html as html
import dash_bootstrap_components as dbc

from app import app

import config
from dash.dependencies import Input, Output, State, ALL
from components import content
from loader.tickets import TicketParser


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return content.overview.page()
    elif pathname.startswith("/process"):
        filename = pathname.strip("/process").strip("/")
        ticket_parser = TicketParser(filename)
        if filename == '':
            data = {
                "form": ticket_parser.empty_data(),
                "image": None
            }
        else:
            data = TicketParser(filename).parse()
        return content.process.page(data)
    elif pathname == "/history":
        return content.history.page()

    # If the user tries to reach a different page, return a 404 message
    return dbc.Card(
        [
            html.H1("404: Not found", className="text-danger"),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )
