import os
import dash.html as html
import dash_bootstrap_components as dbc
from urllib import parse

import pandas as pd

from app import app

import dash
from dash import Input, Output, State, ALL, callback
from docxtpl import DocxTemplate

from src.core.config import get_settings

settings = get_settings()


@callback(
    Output('results-save', "children"),
    Input('ticket-save', "n_clicks"),
    Input({'type': 'parser', 'index': ALL}, 'value'),
    State("url", "pathname")
)
def ticket_save(ticket_generate, parser_data, pathname):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == 'ticket-save':
        data_path = os.path.join(settings.OUTPUT_PATH, "data.csv")
        if os.path.exists(data_path):
            data = pd.read_csv(data_path).set_index("case_id")
        else:
            data = pd.DataFrame()
        context = {
            k.replace(
                '{"index":"parser-', ""
            ).replace(
                '","type":"parser"}.value', ""
            ).replace("-", "_"): v for k, v in
            ctx.inputs.items() if "n_clicks" not in k
        }
        data_new = pd.DataFrame([context]).set_index("case_id")
        data = pd.concat([data, data_new])
        data = data[~data.index.duplicated(keep='last')]
        if pathname.startswith("/process"):
            filename = pathname.strip("/process").strip("/")
            os.remove(os.path.join(settings.UPLOAD_PATH, filename))
        data.to_csv(data_path)
        return html.P("Data saved !")


@callback(
    Output('results-generate', "children"),
    Input('ticket-generate', "n_clicks"),
    Input({'type': 'parser', 'index': ALL}, 'value'),
)
def ticket_generate(ticket_generate, parser_data):
    # If the user tries to reach a different page, return a 404 message
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == 'ticket-generate':
        doc = DocxTemplate(
            os.path.join(settings.CONFIG_PATH, "4.entry_of_appearance.docx")
        )
        context = {
            k.replace(
                '{"index":"parser-', ""
            ).replace(
                '","type":"parser"}.value', ""
            ).replace("-", "_"): v for k, v in
            ctx.inputs.items() if "n_clicks" not in k
        }
        doc.render(context)
        doc.save(os.path.join(settings.OUTPUT_PATH,
                              f"4.entry_of_appearance_"
                              f"{context.get('case_id')}.docx"))

        return [
            "Your file is ready : ",
            dbc.CardLink(html.A("Link",
                                href=f"/documents/4.entry_of_appearance_"
                                     f"{context.get('case_id')}.docx"))
        ]
