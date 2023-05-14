from urllib import parse

import dash.html as html
import dash_bootstrap_components as dbc
from dash import Input, Output, callback

from loader.tickets import TicketParser
from src.components import content
from src.core.config import get_settings

settings = get_settings()


@callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return content.overview.page()
    elif pathname.startswith("/process"):
        filename = pathname.strip("/process").strip("/")
        ticket_parser = TicketParser(filename)
        if filename == "":
            data = {
                "form": ticket_parser.get_fields(results={}),
                "image": None,
            }
        else:
            filename = parse.unquote(filename)
            data = TicketParser(filename).parse()
        return dbc.Row(content.process.page(data))
    elif pathname == "/history":
        return content.history.page()
    elif pathname == "/leads":
        return content.leads.page()
    elif "/leads/single" in pathname:
        return content.leads.single()
    elif pathname == "/stats":
        return content.stats.page()

    # If the user tries to reach a different page, return a 404 message
    return dbc.Card(
        [
            html.H1("404: Not found", className="text-danger"),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )
