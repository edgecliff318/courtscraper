import logging

import dash_bootstrap_components as dbc
from dash import dcc, html
import dash_mantine_components as dmc
import pandas as pd

from src.components.inputs import generate_form_group
from src.models import leads as leads_model

logger = logging.Logger(__name__)


import re
from src.services import messages as messages_service


def extract_case_id(text):
    pattern = r"\[(\d+)\]"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def get_conversation(df: pd.DataFrame) -> list:
    case_id = extract_case_id(df["Case ID"].iloc[0])

    messages = messages_service.get_interactions(case_id=case_id)
    df_conversation = pd.DataFrame([message.model_dump() for message in messages])
    df_conversation["creation_date"] = pd.to_datetime(
        df_conversation["creation_date"], utc=True
    )
    df_conversation.sort_values(by=["creation_date"], inplace=True, ascending=True)
    df_conversation["creation_date"] = df_conversation["creation_date"].dt.tz_convert(
        "US/Central"
    )
    df_conversation = df_conversation[["direction", "message", "creation_date"]]
    return df_conversation.to_dict("records")


def create_chat_bubble(text, from_user=True):
    return html.Div(
        children=[dcc.Markdown(text)],
        style={
            "maxWidth": "60%",
            "backgroundColor": "#DCF8C6" if from_user else "#F0F0F0",
            "padding": "10px",
            "borderRadius": "15px",
            "margin": "5px",
            "textAlign": "left",
            "marginLeft": "0" if from_user else "auto",
            "marginRight": "auto" if from_user else "0",
            "wordBreak": "break-word",
        },
    )


def create_chat(df: pd.DataFrame):
    list_of_messages = get_conversation(df)

    return html.Div(
        [
            dmc.Container(
              
                [
                    create_chat_bubble(
                        message["message"],
                        from_user=True if message["direction"] == "outbound" else False,
                    )
                    for message in list_of_messages
                ],
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "maxWidth": "500px",
                    "margin": "auto",
                    "paddingTop": "10px",
                    "maxHeight": "50vh",
                    "overflowY": "scroll",
                },
            )
        ],
        style={
            "height": "100vh",
            "backgroundColor": "#E5E5E5",
            "padding": "20px",
            "maxHeight": "50vh",
            "overflowY": "scroll",
        },
    )


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
        ),
    ]


def many_response_model(prefix: str) -> html.Div:
    status_options = generate_status_options(prefix)

    modal_footer_buttons = [
        dmc.Button(text, id=f"{prefix}-{button_id}", className="ml-auto", color=color)
        for text, button_id, color in [
            ("Update Status", "modal-lead-status-update", "dark"),
            ("Generate Letters", "generate-letters", "dark"),
            ("Send ", "send-all", "green"),
            ("Cancel", "send-all-cases", "red"),
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
                    dbc.Row(
                        id=f"{prefix}-modal-content-generate-letters-status",
                        className="m-2",
                    ),
                    dbc.ModalFooter(
                        modal_footer_buttons, className="d-flex justify-content-end"
                    ),
                ],
                id=f"{prefix}-modal",
                size="xl",
            ),
        ],
        className="m-3",
    )


def messaging_template(df, prefix: str = "outbound"):
   
    import dash
    ctx = dash.callback_context
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id == "conversation-response-many":
        grid = create_chat(df)
    else:
        import dash_ag_grid as dag
        if 'First Name'  in df.columns and 'Last Name'  in df.columns:
            cols = ['First Name', 'Last Name', 'Phone']
        else:
            cols = ['Phone']
        df = df[cols]
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
        ]
    )
