import logging
import re

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
from dash import dcc, html
from dash_iconify import DashIconify

from src.components.inputs import generate_form_group
from src.models import leads as leads_model
from src.services import messages as messages_service

logger = logging.Logger(__name__)


def extract_case_id(text):
    pattern = r"\[(.*?)\]"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def create_single_selection_alert():
    return dmc.Alert(
        "Please select just one row to show the conversion.",
        title="Alert: Multiple Selections!",
        color="red",
    )


def get_conversation(df: pd.DataFrame, phone=None) -> list:
    case_id = extract_case_id(df["Case ID"].iloc[0])

    messages = messages_service.get_interactions(case_id=case_id)
    if phone is not None:
        messages = [
            message
            for message in messages
            if message.phone is not None and (message.phone[-4:] == phone[-4:])
        ]
    df_conversation = pd.DataFrame(
        [message.model_dump() for message in messages]
    )
    df_conversation["creation_date"] = pd.to_datetime(
        df_conversation["creation_date"], utc=True
    )
    df_conversation.sort_values(
        by=["creation_date"], inplace=True, ascending=True
    )
    df_conversation["creation_date"] = df_conversation[
        "creation_date"
    ].dt.tz_convert("US/Central")
    df_conversation = df_conversation[
        ["direction", "message", "creation_date"]
    ]
    return df_conversation.to_dict("records")


def create_chat_bubble(text, from_user=True, date=None):
    return html.Div(
        children=[
            dcc.Markdown(text),
            dmc.Text(
                date.strftime("%Y-%m-%d %H:%M:%S") if date is not None else "",
                size="xs",
                color="gray",
            ),
        ],
        style={
            "maxWidth": "60%",
            "backgroundColor": "#F0F0F0" if from_user else "#DCF8C6",
            "padding": "10px",
            "borderRadius": "15px",
            "margin": "5px",
            "textAlign": "left",
            "marginLeft": "0" if from_user else "auto",
            "marginRight": "auto" if from_user else "0",
            "wordBreak": "break-word",
        },
    )


def create_chat(df: pd.DataFrame, phone=None):
    list_of_messages = get_conversation(df, phone=phone)

    return html.Div(
        [
            dmc.Container(
                [
                    create_chat_bubble(
                        message["message"],
                        from_user=(
                            True
                            if message["direction"] == "outbound"
                            else False
                        ),
                        date=message["creation_date"],
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
            "maxHeight": "54vh",
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


def many_response_model(prefix: str) -> html.Div:
    status_options = generate_status_options(prefix)

    modal_footer_buttons = [
        dmc.Button(
            text, id=f"{prefix}-{button_id}", className="ml-auto", color=color
        )
        for text, button_id, color in [
            ("Update Status", "modal-lead-status-update", "dark"),
            ("Generate Letters", "generate-letters", "dark"),
            ("Send ", "send-all", "green"),
            ("Cancel", "all-cancel", "red"),
        ]
    ]

    return html.Div(
        [
            dcc.Store(id=f"{prefix}-memory", storage_type="memory"),
            dbc.Modal(
                [
                    dbc.ModalHeader("More information about the selected SMS"),
                    dbc.ModalBody(
                        messaging_template(
                            pd.DataFrame(columns=["Phone"], data=[]),
                            prefix=prefix,
                        ),
                        id=f"{prefix}-modal-content",
                    ),
                    html.Div(
                        id=f"{prefix}-hidden-div", style={"display": "none"}
                    ),
                    html.Div(id=f"{prefix}-modal-content-sending-status"),
                    dbc.Row(status_options, className="m-2"),
                    dbc.Row(id=f"{prefix}-modal-lead-status-update-status"),
                    dbc.Row(
                        id=f"{prefix}-modal-content-generate-letters-status",
                        className="m-2",
                    ),
                    dbc.ModalFooter(
                        modal_footer_buttons,
                        className="d-flex justify-content-end",
                    ),
                ],
                id=f"{prefix}-modal",
                size="xl",
            ),
        ],
        className="m-3",
    )


def messaging_template(
    df, prefix: str = "outbound", many_responses: bool = False
):
    title = None
    if many_responses:
        num_row = df.SID.nunique()
        if num_row != 1:
            return create_single_selection_alert()
        else:
            first_phone = df["Phone"].iloc[0]
            title = dmc.Alert(
                f"{first_phone}",
                title="Phone Number",
                icon=DashIconify(icon="ph:phone-bold"),
                color="violet",
                className="my-3 p-3",
            )
            grid = create_chat(df, phone=first_phone)
    else:
        if "First Name" in df.columns and "Last Name" in df.columns:
            cols = ["First Name", "Last Name", "Phone"]
        else:
            cols = ["Phone"]
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
            dbc.Col([title, grid], className="mb-2", width=6),
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
