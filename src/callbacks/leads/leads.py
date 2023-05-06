import logging

import dash
import dash.html as html
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, html, dcc, ctx, callback

from src.components.inputs import generate_form_group


from src.core.config import get_settings
from src.services import leads

logger = logging.Logger(__name__)

settings = get_settings()


@callback(
    Output("leads-data", "children"),
    Input("leads-button", "n_clicks"),
    Input("court-selector", "value"),
    Input("date-selector", "start_date"),
    Input("date-selector", "end_date"),
    Input("lead-status-selector", "value"),
)
def render_leads(search, court_code_list, start_date, end_date, status):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    grid = "Empty"
    if trigger_id == "leads-button":
        if status == "all":
            status = None
        leads_list = leads.get_leads(
            court_code_list, start_date, end_date, status
        )
        df = pd.DataFrame([lead.dict() for lead in leads_list])

        if df.empty:
            return [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("Leads", className="card-title"),
                                "No leads found",
                            ]
                        ),
                    ),
                    width=12,
                    className="mb-2",
                )
            ]

        df["case_date"] = df["case_date"].dt.strftime("%m/%d/%Y")

        df = df[
            [
                "case_id",
                "case_date",
                "first_name",
                "last_name",
                "phone",
                "email",
                "status",
                "age",
                "charges",
                "disposition",
            ]
        ].set_index("case_id")

        df = df.rename(
            columns={
                "first_name": "First Name",
                "last_name": "Last Name",
                "phone": "Phone",
                "email": "Email",
                "status": "Status",
                "age": "Age",
                "charges": "Charges",
                "disposition": "Disposition",
                "case_date": "Date",
            }
        )
        df.index.name = "Case ID"

        df.reset_index(inplace=True)
        df["Case ID"] = df["Case ID"].map(lambda x: f"[{x}](/case/{x})")

        column_defs = [
            {
                "headerName": "Case ID",
                "field": "Case ID",
                "editable": False,
                "filter": "agTextColumnFilter",
                "sortable": True,
                "resizable": True,
                "flex": 1,
                "cellRenderer": "markdown",
            }
        ] + [
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
            if col != "Case ID"
        ]

        grid = dag.AgGrid(
            id="portfolio-grid",
            columnDefs=column_defs,
            rowData=df.to_dict("records"),
            columnSize="sizeToFit",
            dashGridOptions={
                "undoRedoCellEditing": True,
                "rowSelection": "single",
                "rowSelection":"multiple", "rowMultiSelectWithClick": True
                # "rowSelection": "single"

            },
        )
    return [
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div([html.H3("Cases", className="card-title"),dbc.Button("Cases Process", id="cases-process", className="card-title")], className="d-flex justify-content-between"),
                       
                        grid,
                    ]
                ),
            ),
            width=12,
            className="mb-2",
        )

    ]

# # ### Multi Select Rows 
# # @callback(
# #     Output("selections-multiple-click-output", "children"),
# #     Input("portfolio-grid", "selectedRows"),
# # )
# # def selected(selected):
# #     if selected:
# #         return f"You selected : {selected}"
# #     return ""



# def messaging_template():
#     return html.Div(
#         [
#             dbc.Row(
#                 [
#                     dbc.Col(
#                         generate_form_group(
#                             label="Sample Message",
#                             id="lead-single-message-selector",
#                             placeholder="Select a Sample Message",
#                             type="Dropdown",
#                             options=[],
#                             persistence_type="session",
#                             persistence=True,
#                         ),
#                         width=8,
#                     ),
#                 ],
#                 className="mb-1",
#             ),
#             dbc.Row(
#                 [
#                     dbc.Col(html.Div([
#                         dbc.RadioButton(
#                             id="lead-media-enabled",
#                             persistence_type="session",
#                             persistence=True,
#                             value=False,
#                         ),
#                         html.Label("Include a Case Copy"),
#                                                 # html.Div([html.H3("Cases", className="card-title"),dbc.Button("Cases Process", id="cases-process", className="card-title")], className="d-flex justify-content-between"),

#                         ],  className="d-flex justify-content-start"),
#                         width=8,
#                     ),
#                 ],
#                 className="mb-1",
#             ),
#             # dbc.Row(
#             #     [
#             #         dbc.Col(
#             #             [
#             #                 generate_form_group(
#             #                     label="Phone Number",
#             #                     id="lead-single-been-verified-phone",
#             #                     placeholder="Set the phone number",
#             #                     type="Input",
#             #                     persistence_type="session",
#             #                     persistence=True,
#             #                 )
#             #             ],
#             #             width=8,
#             #         ),
#             #     ],
#             #     className="mb-1",
#             # ),
#             dbc.Row(
#                 [
#                     dbc.Col(
#                         generate_form_group(
#                             label="Message",
#                             id="lead-single-message",
#                             placeholder="Type in the message",
#                             type="Textarea",
#                             style={"height": 300},
#                         ),
#                         width=8,
#                     ),
#                 ]
#             ),
#             dbc.Row([dbc.Col(id="lead-single-message-status")]),
#         ],
#         className="d-flex flex-column justify-content-between justify-content-center",
#     )


# @callback(
#     Output("modal", "is_open"),
#     Output("modal-content", "children"),
#     Input("portfolio-grid", "selectedRows"),
#     # Input("close", "n_clicks"),
#     Input("cases-process", "n_clicks"),
    
# )
# def open_modal(selection, _):
#     print("open_modal\n\n\n")
#     if ctx.triggered_id == "close":
#         return False, dash.no_update
#     if selection and ctx.triggered_id == "cases-process":
#         # return True, f"You selected {str(selection)}"
#         return True, messaging_template()

#     return dash.no_update, dash.no_update
