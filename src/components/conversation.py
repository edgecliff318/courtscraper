import logging

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import dash_ag_grid as dag
import dash_mantine_components as dmc


from src.components.filters import leads_controls
from src.components.inputs import generate_form_group
from src.models import leads as leads_model

logger = logging.Logger(__name__)





def generate_status_options(prefix: str):
    return [
        dbc.Col("Update the leads status", width=3),
        dbc.Col(
            generate_form_group(
                label="Update the leads status",
                id=f"{prefix}-modal-lead-status",
                placeholder="Set the status",
                type="Dropdown",
                options=[o for o in leads_model.leads_statuses if o["value"] != "all"],
                persistence_type="session",
                persistence=True,
            ),
            width=4,
        )
    ]

def many_response_model(prefix: str) -> html.Div:
    status_options = generate_status_options(prefix)

    modal_footer_buttons = [
        dmc.Button(
            text,
            id=f"{prefix}-{button_id}",
            className="ml-auto",
            color=color
        )
        for text, button_id, color in [
            ("Update Status", "modal-lead-status-update", "dark"),
            ("Generate Letters", "generate-letters", "dark"),
            ("Send all cases", "send-all", "green"),
            ("Cancel", "send-all-cases", "red")
        ]
    ]

    return html.Div(
        [
            dcc.Store(id=f"{prefix}-memory", storage_type="memory"),
            dbc.Modal(
                [
                    dbc.ModalHeader("More information about selected row"),
                    dbc.ModalBody(id=f"{prefix}-modal-content"),
                    html.Div(id=f"{prefix}-hidden-div", style={"display": "none"}),
                    html.Div(id=f"{prefix}-modal-content-sending-status"),
                    dbc.Row(status_options, className="m-2"),
                    dbc.Row(id=f"{prefix}-modal-lead-status-update-status"),
                    dbc.Row(id=f"{prefix}-modal-content-generate-letters-status", className="m-2"),
                    dbc.ModalFooter(modal_footer_buttons, className="d-flex justify-content-end"),
                ],
                id=f"{prefix}-modal",
                size="xl",
            )
        ],
        className="m-3",
    )



def messaging_template(df, prefix: str = "outbound"):
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
        id=f"{prefix}-portfolio-grid-multiple-selected",
        columnDefs=column_defs,
        rowData=df.to_dict("records"),
        columnSize="sizeToFit",
        dashGridOptions={
            "undoRedoCellEditing": True,
        },
    )

    msg = html.Div(
        [
            dbc.Row(
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
                    dbc.Col(
                        html.Div(
                            [
                                dbc.RadioButton(
                                    id="lead-media-enabled-modal",
                                    persistence_type="session",
                                    persistence=True,
                                    value=False,
                                ),
                                html.Label("Include a Case Copy"),
                            ],
                            className="d-flex justify-content-start",
                        ),
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
                            minRows=10,
                        ),
                        width=10,
                    ),
                ]
            ),
        ]
    )
    return html.Div(
        [
            dbc.Col([msg], className="mb-2", width=6),
            dbc.Col([grid], className="mb-2", width=6),
        ],
        className="d-flex justify-content-between",
    )


def conversation_model():
    
    status_options = [
        dbc.Col("Update the leads status", width=3),
        dbc.Col(
            generate_form_group(
                label="Update the leads status",
                id="modal-lead-status",
                placeholder="Set the status",
                type="Dropdown",
                options=[
                    o
                    for o in leads_model.leads_statuses
                    if o["value"] != "all"
                ],
                persistence_type="session",
                persistence=True,
            ),
            width=4,
        ),
    ]
    return html.Div(
        [
            html.Div(
                dbc.Modal(
                    [
                        dbc.ModalHeader("Conversation"),
                        dbc.ModalBody(id="modal-conversation-content"),
                       
                    ],
                    id="modal-conversation",
                    size="xl",
                ),
                className="m-3",
            ),
            # dbc.Row(
            #     [
            #         dbc.Col(
            #             dbc.Card(
            #                 dbc.CardBody(
            #                     [
            #                         leads_controls,
            #                     ]
            #                 ),
            #             ),
            #             width=12,
            #             className="mb-2",
            #         ),
            #     ]
            # ),
            # dbc.Row([], id="cases-data"),
            # dbc.Row([], id="leads-data"),
            # dbc.Row([html.Div(id="selections-multiple-click-output")]),
        ]
    )
