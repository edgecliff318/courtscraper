import logging

import dash
import dash.html as html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, html, dcc, ctx, callback,State

from src.components.inputs import generate_form_group


from src.core.config import get_settings
from src.services import leads

logger = logging.Logger(__name__)

settings = get_settings()

def messaging_template(df):
    column_defs = [
        {
                "headerName": col,
                "field": col,
                "editable": True,
                "filter": "agTextColumnFilter",
                "sortable": True,
                "resizable": True,
                "flex": 1,
            }
            for col in df.columns
        ]
    grid = dag.AgGrid(
            id="portfolio-grid-multiple-selected",
            columnDefs=column_defs,
            rowData=df.to_dict("records"),
            columnSize="sizeToFit",
            dashGridOptions={
                "undoRedoCellEditing": True,
            },
        )
    
    msg = html.Div(
        [dbc.Row(
                [
                    dbc.Col(
                        generate_form_group(
                            label="Sample Message",
                            id="lead-single-message-selector-modal",
                            placeholder="Select a Sample Message",
                            type="Dropdown",
                            options=[],
                            persistence_type="session",
                            persistence=True,
                        ),
                        width=10,
                    ),
                ],
                className="mb-1",
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div([
                        dbc.RadioButton(
                            id="lead-media-enabled-modal",
                            persistence_type="session",
                            persistence=True,
                            value=False,
                        ),
                        html.Label("Include a Case Copy"),
                        ],  className="d-flex justify-content-start"),
                        width=10,
                    ),
                ],
                className="mb-1",
            ),
           
            dbc.Row(
                [
                    dbc.Col(
                        generate_form_group(
                            label="Message",
                            id="lead-single-message-modal",
                            placeholder="Type in the message",
                            type="Textarea",
                            style={"height": 300},
                        ),
                        width=10,
                    ),
                ]
            )]
    )
    return html.Div(
        [
            dbc.Col([msg], className="mb-2", width=6),
            dbc.Col([grid], className="mb-2", width=6),
        ],
        className="d-flex justify-content-between",
    )


@callback(
    Output("modal", "is_open"),
    Output("modal-content", "children"),
    Output('memory', 'data'),
    Input("portfolio-grid", "selectedRows"),
    Input("send-all-cases", "n_clicks"),
    Input("cases-process", "n_clicks"),
    State('memory', 'data'),

    
)
def open_modal(selection, _, __, data):
    print(f"open_moda: {data}l\n\n\n")
    
    
    
    
    # if ctx.triggered_id == "send-all-cases":
    #     return False, dash.no_update
    if selection and ctx.triggered_id == "cases-process":
        # return True, f"You selected {str(selection)}"
        df = pd.DataFrame(selection)
        df_filter = df[["First Name","Last Name", "Phone"]]
        if data is None:
            data = {'df': df.to_dict("records")}
        else:
            data['df'] = df.to_dict("records")
        return True, messaging_template(df_filter), data

    return dash.no_update, dash.no_update , dash.no_update
